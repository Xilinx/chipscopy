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

from chipscopy.tcf.services import svf, DoneHWCommand


class svfProxy(svf.SVFService):
    """TCF SVF service interface."""

    def add_target(self, name: str, done: DoneHWCommand) -> None:
        args = {"name": name}
        return self.send_xicom_command("reqAddTarget", args, done)

    def add_device(self, target_ctx: str, name: str, done: DoneHWCommand) -> str:
        args = {"ctx": target_ctx, "name": name}
        return self.send_xicom_command("reqAddDevice", args, done)

    def remove_target(self, target_ctx: str, done: DoneHWCommand) -> None:
        args = {"ctx": target_ctx}
        return self.send_xicom_command("reqRemoveTarget", args, done)
