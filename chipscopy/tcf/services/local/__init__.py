# *****************************************************************************
# * Modifications Copyright (C) 2021-2022, Xilinx, Inc., All rights reserved.
# * Modifications Copyright (C) 2022-2026, Advanced Micro Devices, Inc., All rights reserved..
# *
# * Copyright (c) 2011, 2013 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *     Xilinx
# *****************************************************************************

try:
    import pytcf
    from ...native.services.local import *
except:
    import re
    import time
    from typing import ClassVar
    from ... import channel, transport
    from ...channel import fromJSONSequence, toJSONSequence
    from .. import to_xargs, from_xargs, ServiceProvider, Service, add_service_provider


    class CommandRequest(object):
        def __init__(self, _channel, token, data, node=None):
            self.channel = _channel
            self.token = token
            self.data = data
            if node is not None:
                self.node = node
            # Splice the xargs binary side-channel here, so `req.args` means the
            # same thing on every transport: the fully decoded argument list.
            # pytcf and the Rust bridge both hand it over already decoded, and
            # services therefore no longer call from_xargs themselves.
            self.args = from_xargs(fromJSONSequence(data)) if data else None

        def sendError(self, error, *result):
            if type(error) is list:
                error_props = {
                    "Code": 0x20001,  # ERR_OTHER default used by hw_server
                    "Time": int(time.perf_counter() * 1000),
                    "Format": str(error),
                }
            else:
                error_props = {
                    "Code": 0x20001,  # ERR_OTHER default used by hw_server
                    "Time": int(time.perf_counter() * 1000),
                    "Format": str(error),
                    "Class": error.__class__.__name__,
                    "Module": error.__class__.__module__
                }
            self.channel.sendResult(self.token, toJSONSequence((error_props, *result)))

        def sendResult(self, *result):
            self.channel.sendResult(self.token, toJSONSequence((None, *result)))

        def sendXicomResult(self, *results):
            result = to_xargs(results)
            self.channel.sendResult(self.token, toJSONSequence((None, *result)))

        def sendXicomProgress(self, *progress):
            args = to_xargs(progress)
            self.channel.sendProgress(self.token, toJSONSequence((None, *args)))


    def send_xicom_event(service_name, event_name, args):
        data = toJSONSequence(to_xargs(args))
        transport.sendEvent(service_name, event_name, data)


    def to_snake_case(name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


    class CommandServer(channel.CommandServer):
        def __init__(self, service, _channel):
            self.service = service
            self.channel = _channel

        def command(self, token, name, data):
            cmd = getattr(self.service, to_snake_case(name) + "_cmd", None)
            if not cmd:
                cmd = getattr(self.service, name + 'Cmd', None)
            if cmd:
                try:
                    request = CommandRequest(self.channel, token, data)
                    cmd(request)
                except Exception as x:
                    msg = f'ChipScope Service {self.service.getName()} {name}: {x}.'
                    request.sendError(msg)
            else:
                channel.rejectCommand(token)


    class LocalServiceProvider(ServiceProvider):
        def __init__(self, service):
            self.service = service

        def get_local_service(self, _channel):
            _channel.addCommandServer(
                self.service,
                CommandServer(self.service, _channel)
            )
            return self.service,


    _local_services_added = set()


    def add_local_service(service: Service or ClassVar[Service]):
        if str(service) not in _local_services_added:
            add_service_provider(LocalServiceProvider(service))
            _local_services_added.add(str(service))


# ---------------------------------------------------------------------------
# tcf-rs transport override
#
# When running inside the chipscope-pyrs server, the Rust `tcf_rs` bridge module
# is importable. In that case the incoming-command dispatch is driven by the Rust
# TCF event loop, which calls a registered handler `(token, channel, data)` where
# `channel` is a bridge channel handle and `data` the raw argument bytes. We keep
# chipscopy's own byte-level codec (`toJSONSequence`/`fromJSONSequence`): the
# bridge only moves raw payloads. These definitions shadow the pure-Python ones
# above; standalone chipscopy has no `tcf_rs`, so this block is skipped.
# ---------------------------------------------------------------------------
try:
    import tcf_rs as _tcf_rs
except ImportError:
    _tcf_rs = None

if _tcf_rs is not None:
    # Object-level bridge: Python hands Rust plain Python objects and does no
    # formatting. Rust decodes the wire into a Python list (req.args) and, on the
    # way out, writes the error slot, applies the xargs binary side-channel and
    # encodes the sequence — so there is no toJSONSequence/fromJSONSequence, no
    # hand-built `(None, *result)` and no to_xargs call here.
    class CommandRequest(object):
        def __init__(self, _channel, token, args, node=None):
            self.channel = _channel  # bridge server-channel handle
            self.token = token
            self.data = args
            if node is not None:
                self.node = node
            self.args = args  # already the decoded argument list

        def sendError(self, error, *result):
            # Rust builds the error object from `error` itself, keeping Class and
            # Module so the client can reconstruct the exception type.
            self.channel.send_error(self.token, error, result)

        def sendResult(self, *result):
            self.channel.send_result(self.token, result)

        def sendXicomResult(self, *results):
            self.channel.send_xicom_result(self.token, results)

        def sendXicomProgress(self, *progress):
            self.channel.send_xicom_progress(self.token, progress)

    def send_xicom_event(service_name, event_name, args):
        # Node property dicts routinely carry bytes, which is what the side
        # channel exists to extract; Rust applies it.
        _tcf_rs.send_event(service_name, event_name, args, xicom=True)

    def _to_camel_case(name):
        m = name.split("_")
        return m[0] + "".join(i.title() for i in m[1:-1])

    def _wrap_command(callback):
        def handle_command(token, channel, args):
            callback(CommandRequest(channel, token, args))
        return handle_command

    _local_services_added = set()

    def add_local_service(service):
        convert_camel_case = getattr(service, "convert_camel_case", True)
        if str(service) in _local_services_added:
            return
        _local_services_added.add(str(service))
        for c in [c for c in dir(service)
                  if not c.startswith("__") and c.endswith("_cmd")]:
            name = _to_camel_case(c) if convert_camel_case else c[:c.find("_cmd")]
            _tcf_rs.add_command_handler(
                service.getName(), name, _wrap_command(getattr(service, c))
            )
        for c in [c for c in dir(service)
                  if not c.startswith("__") and c.endswith("Cmd")]:
            name = c[:c.find("Cmd")]
            _tcf_rs.add_command_handler(
                service.getName(), name, _wrap_command(getattr(service, c))
            )
