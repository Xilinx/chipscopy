# Copyright 2021 Xilinx, Inc.
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

from typing import List
from chipscopy.dm import jtag, memory, request, NodeAutoUpgrader
from chipscopy.tcf.services import xicom
from ..jtagdevice import JtagDevice, JtagCable
from ..mem import MemoryNode


def find_pmc_tap(hws):
    view = hws.get_view(jtag)
    for node in view.get_all():
        if JtagDevice.is_compatible(node) and (
            node.arch_name and (node.arch_name == "everest" or node.arch_name == "versal")
        ):
            return view.get_node(node.ctx, JtagDevice)
    raise (Exception("Could not find pmc_tap"))


def find_jtag_device(hws):
    view = hws.get_view(jtag)
    for node in view.get_all():
        if JtagDevice.is_compatible(node):
            return view.get_node(node.ctx, JtagDevice)
    raise (Exception("Could not find pmc_tap"))


class PmcTapUtil(JtagDevice):
    def status(self, reg_names: List[str] = ("jtag_status",), done: request.DoneCallback = None):
        """
        Gets status values of registers available on the pmc_tap.
        :param reg_names: Names of desired registers
        :param done: DoneRequest callback
        :return: Token of request
        """
        proc = self.manager.channel.getRemoteService("XicomEverest")
        done = request._make_callback(done)
        node = self
        need_definitions = False

        if "status" not in self.props:
            self.props["status"] = {}
        for name in reg_names:
            if self.get_def_name(name) not in self.props["status"].keys():
                need_definitions = True
                break

        class DoneCmd(xicom.DoneXicom):
            def doneHW(self, token, error, props):
                print("Props:", props)
                if not error:
                    node["status"].update(props)
                    _print_regs(node["status"])
                node.remove_pending(token)  # done state change
                done.done_request(token, error, props)

        # add pending to indicate that this node is being changed
        return self.add_pending(proc.get_status(self.ctx, need_definitions, DoneCmd()))


def _print_regs(regs):
    for reg_name, reg_value in regs.items():
        if isinstance(reg_value, bytearray):
            definition = reg_name + "_definition"
            if definition in regs.keys():
                print(f"\n{reg_name.upper()}")
                print("-" * 60)
                _print_defs(regs[definition], reg_value)
            else:
                reg_value = bytearray(reg_value)
                reg_value.reverse()
                print(f"{reg_name.upper()}: {reg_value.hex()}")


def _to_bits(data):
    return "".join(str((byte >> b) & 1) for byte in data for b in range(8))


def _get_bits(bits, select):
    first, _, last = select.partition(":")
    first = int(first)
    last = int(last) if last else first
    if last < first:
        return bits[first : last - 1 : -1]
    return bits[first : last + 1]


FIELD_WIDTH = 20
BIT_WIDTH = 8


def _print_defs(defs, data):
    bits = _to_bits(data)
    print("{} {} {}".format("Bit".ljust(BIT_WIDTH, " "), "Field".rjust(FIELD_WIDTH, " "), "Value"))
    for bit_range, bit_name in zip(defs["bit_range"], defs["bit_name"]):
        print(
            "{} {} {}".format(
                bit_range.ljust(BIT_WIDTH, " "),
                bit_name.rjust(FIELD_WIDTH, " "),
                _get_bits(bits, bit_range),
            )
        )


class JtagNodeAutoUpgrader(NodeAutoUpgrader):
    def __call__(self, node, **kwargs):
        if JtagCable.is_compatible(node):
            node = node.manager.upgrade_node(node, JtagCable)
        elif JtagDevice.is_compatible(node):
            node = node.manager.upgrade_node(node, JtagDevice)
        node["node_cls"] = node.__class__
        return node


class MemoryNodeAutoUpgrader(NodeAutoUpgrader):
    def __call__(self, node, **kwargs):
        if MemoryNode.is_compatible(node):
            node = node.manager.upgrade_node(node, MemoryNode)
        node["node_cls"] = node.__class__
        return node


def init_config():
    if not jtag.JtagManager.node_auto_upgrader:
        jtag.JtagManager.node_auto_upgrader = JtagNodeAutoUpgrader()
    if not memory.MemoryManager.node_auto_upgrader:
        memory.MemoryManager.node_auto_upgrader = MemoryNodeAutoUpgrader()


def test():
    from chipscopy import client

    # from chipscope.utils import logger
    # logger.enable_domain('view_info')
    # logger.change_log_level("debug")
    hws = client.connect("xcordevl154")
    hws.jtag_target()
    t = hws.jtag_target(index=0)
    return hws, hws.jtag_target(index=1, parent=t)
