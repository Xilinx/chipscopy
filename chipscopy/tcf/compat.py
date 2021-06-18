# *****************************************************************************
# * Copyright (c) 2015-2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

import sys
PY3 = sys.version_info[0] == 3


if PY3:
    ints = (int,)
    strings = (str,)
    inttype = int
    longtype = int

    def str2bytes(data):
        if data and isinstance(data[0], str):
            return bytes([ord(c) for c in data])
        elif isinstance(data, bytes):
            return data
        return bytes(data)
else:
    ints = (int, long)  # @UndefinedVariable
    strings = (basestring, str)  # @UndefinedVariable
    inttype = int
    longtype = long  # @UndefinedVariable

    def str2bytes(data):
        if data and isinstance(data[0], str):
            return bytearray([ord(c) for c in data])
        elif isinstance(data, bytearray):
            return data
        return bytearray(data)


def bytes2str(data):
    if data and isinstance(data[0], int):
        return ''.join(chr(b) for b in data)
    return str(data)
