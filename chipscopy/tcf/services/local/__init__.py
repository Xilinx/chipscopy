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

import re
import time
from typing import ClassVar
from ... import channel, transport
from ...channel import fromJSONSequence, toJSONSequence
from .. import to_xargs, ServiceProvider, Service, add_service_provider


class CommandRequest(object):
    def __init__(self, _channel, token, data, node=None):
        self.channel = _channel
        self.token = token
        self.data = data
        if node is not None:
            self.node = node
        self.args = fromJSONSequence(data) if data else None

    def sendError(self, error, *result):
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
