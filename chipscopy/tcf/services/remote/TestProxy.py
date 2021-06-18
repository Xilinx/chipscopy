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

from .. import test


class TestProxy(test.TestService):
    def add_manager(self, manager_name, done):
        return self.send_xicom_command("addManager", (manager_name,), done)

    def remove_manager(self, manager_name, done):
        return self.send_xicom_command("removeManager", (manager_name,), done)

    def add_node(self, manager_name, ctx, props, done):
        return self.send_xicom_command("addNode", (manager_name, ctx, props), done)

    def remove_node(self, manager_name, ctx, done):
        return self.send_xicom_command("removeNode", (manager_name, ctx), done)

    def update_node(self, manager_name, ctx, props, done):
        return self.send_xicom_command("updateNode", (manager_name, ctx, props), done)

    def exit(self, done):
        return self.send_xicom_command("exit", (), done)
