# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
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

import time
import pytcf
from typing import ClassVar
from .. import Service
from ... import protocol


class CommandRequest(object):
    def __init__(self, _channel, token, data, node=None):
        self.channel = _channel
        self.token = token
        self.data = data
        if node is not None:
            self.node = node
        self.args = data

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
        #self.channel.sendResult(self.token, (error_props, *result))
        pytcf.write_response_args(self.token, self.channel, error_props, None)

    def sendResult(self, *result):
        #self.channel.sendResult(self.token, (None, *result))
        pytcf.write_response_args(self.token, self.channel, None, result)

    def sendXicomResult(self, *results):
        #self.channel.sendResult(self.token, (None, *results))
        pytcf.write_response_args(self.token, self.channel, None, results)

    def sendXicomProgress(self, *progress):
        #self.channel.sendProgress(self.token, (None, *progress))
        pytcf.write_progress_args(self.token, self.channel, progress)


def send_xicom_event(service_name, event_name, args):
    protocol.sendEvent(service_name, event_name, args)


def _wrap_command(callback):
    def handle_command(token, channel):
        args = pytcf.read_command_args(channel)
        callback(CommandRequest(channel, token, args))
    return handle_command


def to_camel_case(name: str) -> str:
    m = name.split("_")
    return m[0] + "".join(i.title() for i in m[1:-1])


_local_services_added = set()
_service_interface = None


def init(si):
    global _service_interface
    _service_interface = si


def add_local_service(service: Service or ClassVar[Service]):
    convert_camel_case = True
    if hasattr(service, "convert_camel_case"):
        convert_camel_case = service.convert_camel_case
    if str(service) not in _local_services_added:
        _local_services_added.add(str(service))
        for c in [c for c in dir(service) if not c.startswith("__") and c.endswith("_cmd")]:
            pytcf.add_command_handler(
                _service_interface,
                service.getName(),
                to_camel_case(c) if convert_camel_case else c[:c.find("_cmd")],
                _wrap_command(getattr(service, c))
            )
        for c in [c for c in dir(service) if not c.startswith("__") and c.endswith("Cmd")]:
            pytcf.add_command_handler(
                _service_interface,
                service.getName(),
                c[:c.find("Cmd")],
                _wrap_command(getattr(service, c))
            )
