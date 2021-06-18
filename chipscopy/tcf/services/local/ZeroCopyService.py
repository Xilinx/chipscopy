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

"""
ZeroCopy dummy service to enable ZeroCopy binary transfers
"""

from ... import services
from ... import compat, protocol, services, channel, peer, errors


class ZeroCopyService(services.Service):
    instance = None

    def __init__(self):
        ZeroCopyService.instance = self

    def getName(self):
        return "ZeroCopy"


class ZeroCopyServiceProvider(services.ServiceProvider):
    def get_local_service(self, _channel):
        class CommandServer(channel.CommandServer):
            def command(self, token, name, data):
                pass
        _channel.addCommandServer(ZeroCopyService.instance, CommandServer())
        return (ZeroCopyService.instance,)

ZeroCopyService()
services.add_service_provider(ZeroCopyServiceProvider())