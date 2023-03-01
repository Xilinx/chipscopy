# *****************************************************************************
# * Copyright(C) 2020-2022 Xilinx, Inc.
# * Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

from chipscopy.tcf.services.arguments import *

# from ... import errors, channel
from chipscopy.tcf.channel.Command import Command
from chipscopy.tcf.services import xicom


class XicomEverestProxy(xicom.XicomEverestService):
    def __init__(self, channel):
        super(XicomEverestProxy, self).__init__(channel)
        self.listeners = {}

    def config(self, ctx, data, options={}, done=None):
        args = {'ctx': ctx, "data": data}
        args.update(options)
        return self.send_xicom_command("config", args, done)

    def get_status(self, ctx, need_definitions, done):
        args = {'ctx': ctx, "need_definitions": need_definitions}
        return self.send_xicom_command("status", args, done)

    def get_static(self, ctx, need_definitions, done):
        args = {'ctx': ctx, "need_definitions": need_definitions}
        return self.send_xicom_command("get_static", args, done)

    def reset(self, ctx, done):
        args = {'ctx': ctx}
        return self.send_xicom_command("reset", args, done)

    def test(self, props, done):
        return self.send_xicom_command("test", props, done)
