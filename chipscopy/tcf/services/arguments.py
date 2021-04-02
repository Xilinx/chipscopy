# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

import re
import base64

DEFAULT_ARG_VERSION = "arg_3"

data_count_re = re.compile('\((\d+)\)')


class JsonDataEncoder(object):
    def __init__(self, data):
        self.data = data

    def __json__(self):
        return "({})".format(len(self.data))

    def __str__(self):
        return self.__json__()

    def __repr__(self):
        return self.__json__()

def preprocess_list(items):
    l = []
    data = bytearray()
    for v in items:
        t = type(v)
        if t == dict:
            v, d = preprocess_props(v)
            data += d
        elif t == bytearray or t == bytes:
            data += v
            v = JsonDataEncoder(v)
        l.append(v)
    return l, data


def preprocess_props(props):
    out_props = {}
    data = bytearray()
    for k, v in props.items():
        t = type(v)
        if t == bytearray or t == bytes:
            data += v
            v = JsonDataEncoder(v)
        elif t == dict:
            v, d = preprocess_props(v)
            data += d
        elif t == list:
            v, d = preprocess_list(v)
            data += d
        out_props[k] = v
    return out_props, data


def args_from_props(**props):
    args, data = preprocess_props(props)
    return DEFAULT_ARG_VERSION, args, data


def to_xargs(args):
    xargs = []
    if type(args) == dict:
        props, data = preprocess_props(args)
        xargs.append(props)
        if len(data) > 0:
            xargs.append(data)
    else:
        for arg in args:
            if type(arg) == dict:
                props, data = preprocess_props(arg)
                xargs.append(props)
                if len(data) > 0:
                    xargs.append(data)
            elif isinstance(arg, list) or isinstance(arg, tuple):
                arg, data = preprocess_list(arg)
                xargs.append(arg)
                if len(data) > 0:
                    xargs.append(data)
            else:
                xargs.append(arg)
    return xargs


class ArgDataParser(object):
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def __call__(self, size):
        end = self.pos + size
        if not isinstance(self.data, bytearray) and not isinstance(self.data, bytes):
            self.data = base64.b64decode(self.data)
        chunk = self.data[self.pos: end]
        self.pos = end
        return chunk


def _dict_from_args(args, parser):
    return {k: _handle_arg_value(v, parser) for k, v in args.items()}


def _handle_arg_value(arg_val, parser):
    t = type(arg_val)
    if t == dict:
        arg_val = _dict_from_args(arg_val, parser)
    elif t == list:
        arg_val = [_handle_arg_value(i, parser) for i in arg_val]
    elif t == str and parser:
        m = data_count_re.match(arg_val)
        if m:
            arg_val = parser(int(m.groups()[0]))
    return arg_val


def props_from_args(args):
    props = from_xargs(args)

    if props and len(props) == 1:
        props = props[0]

    return props


def from_xargs(args):
    props = []
    parser = None

    for i in range(len(args)):
        if args[i] == DEFAULT_ARG_VERSION:
            continue
        elif parser:
            parser = None
            continue
        elif i + 1 < len(args) and \
                (type(args[i + 1]) == bytearray or type(args[i+1]) == str):
            parser = ArgDataParser(args[i + 1])
            props.append(_handle_arg_value(args[i], parser))
            if parser.pos == 0:  # parser unused so don't skip
                parser = None
        # elif type(args[i]) == dict:
        #     if i+1 < len(args) and type(args[i+1]) == bytearray:
        #         parser = ArgDataParser(args[i+1])
        #     props.append(_dict_from_args(args[i], parser))
        else:
            props.append(args[i])
    return props
