# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from chipscopy.tcf.services import Service, DoneHWCommand, Token

NAME = "Test"


class TestProxy(Service):
    def getName(self):
        return NAME

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
