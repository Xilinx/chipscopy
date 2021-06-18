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

import re
from collections import deque

import click
from more_itertools import one

import chipscopy
from chipscopy.api.device.device_scanner import DeviceScanner
from chipscopy import create_session, report_versions, report_devices


class NodeVisitorBase:
    """
    In ChipScoPy, nodes are organized as a tree under a view.
    Example hw_server views are: jtag, memory, debugcore
    Example cs_server views are: chipscope

    Hierarchy:
    server -> view -> node tree

    NodeVisitorBase is a base class that makes visiting nodes easy. Just make a class with the
    NodeVisitorBase as a parent, and define functions with visit_<cls_name> for the node types
    you want to visit. <cls_name> represents the node class type like "JtagDevice", etc.
    """

    def __init__(self, view):
        self._view = view

    def walk(self, node_list=None):
        """
        Recursively walk all nodes in view, including this node
        """
        if node_list is None:
            nodes_to_walk = list(self._view.get_children())
        else:
            nodes_to_walk = list(node_list)

        if len(nodes_to_walk) > 0:
            last_node = nodes_to_walk[-1]
        else:
            last_node = True
        if nodes_to_walk:
            for current_node in nodes_to_walk:
                self._visit(current_node, current_node == last_node)

    def _visit(self, node, is_last_sibling):
        cls = node.props.get("node_cls")
        # Example: <class \'chipscopy.client.jtagdevice.JtagCable\'>
        match = re.fullmatch("^<class \\'(.+)\\'>$", str(cls))
        full_class_name = match.group(1)
        class_name = full_class_name.split(".")[-1]
        method = "_visit_" + class_name
        visitor_method = getattr(self, method, self._visit_default)
        upgraded_node = self._view.get_node(node.ctx, cls)
        assert upgraded_node is not None
        return visitor_method(upgraded_node, is_last_sibling)

    def _visit_default(self, node, is_last_sibling):
        children = list(self._view.get_children(node))
        self.walk(children)

    @staticmethod
    def _print_node_path(node_name, parent_names):
        parent_names = deque(parent_names)
        while parent_names:
            name = parent_names.popleft()
            print(f"{name}/", end="")
        print(f"{node_name}")


# GLOBALS FOR COMMAND LINE MODULE
_hw_url: str
_cs_url: str


def display_banner():
    print(f"\n******** Xilinx ChipScoPy v{chipscopy.__version__}")
    print("  ****** Copyright 2021 Xilinx, Inc. All Rights Reserved.\n")


@click.group()
@click.version_option(version=chipscopy.__version__, message="%(version)s")
@click.option(
    "--hw_url",
    envvar="HW_SERVER_URL",
    default="localhost:3121",
    metavar="<url>",
    show_default=True,
    help="hardware server url",
)
@click.option(
    "--cs_url",
    envvar="CS_SERVER_URL",
    default="None",
    metavar="<url>",
    show_default=True,
    help="chipscope server url",
)
def _chipscopy(hw_url, cs_url):
    global _hw_url, _cs_url
    if len(hw_url) == 0 or hw_url.lower() == "none":
        _hw_url = None
    else:
        _hw_url = hw_url
    if len(cs_url) == 0 or cs_url.lower() == "none":
        _cs_url = None
    else:
        _cs_url = cs_url


@click.command()
@click.option("--devices", is_flag=True, help="Report all devices")
@click.option("--servers", is_flag=True, help="Report all server version information")
def report(devices, servers):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    if devices:
        report_devices(session)
    elif servers:
        report_versions(session)
    else:
        print("report command needs an option like --devices or --servers")


def _create_path(device_count, hier_name):
    return f"/device/{device_count}/{hier_name}"


@click.command()
@click.argument("file")
def info(file):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    device_list = session.devices
    device_count = 0
    for device in device_list:
        for (
            server_type,
            view_name,
            name,
            context,
            hier_name,
        ) in device.device_identification.get_target_tuples():
            path = _create_path(device_count, hier_name)
            if path == file or context == file:
                print("target      :", path)
                print("server_type :", server_type)
                print("view        :", view_name)
                print("name        :", name)
                print("context     :", context)
                print("family      :", device.device_identification["family"])
                print("dna         :", hex(device.device_identification["dna"]))
                print("cable       :", device.device_identification["cable_name"])
                print("jtag_index  :", device.device_identification["jtag_index"])
        device_count += 1


@click.command()
@click.option("-l", "--long", is_flag=True, help="long listing including device contexts")
# @click.option("--force-detection", is_flag=True, help="Force debug core detection prior to list")
def ls(long):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    device_list = session.devices
    device_count = 0
    for device in device_list:
        for (
            server_type,
            view_name,
            name,
            context,
            hier_name,
        ) in device.device_identification.get_target_tuples():
            path = _create_path(device_count, hier_name)
            if long:
                print(f"{path:60s} {context}")
            else:
                print(f"{path}")
        device_count += 1


@click.command()
@click.option("--dna", default=None, required=False, help="find device to program with dna")
@click.option("--cable", default=None, required=False, help="jtag cable name")
@click.option(
    "--position", default=None, required=False, help="jtag position in chain (starting index is 0)"
)
@click.argument("file")
def program(file, dna, cable, position):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    args = {}
    if dna:
        args["dna"] = dna
    if cable:
        args["cable"] = cable
    if position:
        args["jtag_index"] = position
    if len(args) > 0:
        device = session.devices.get(**args)
    else:
        device = one(session.devices)

    device_tracker = device.device_identification
    print(f"\n{'Cable':40s} {'Jtag_Index':>10s}   {'Family':15s} {'DNA':30s}")
    print(
        f"{device_tracker['cable_name']:40s} "
        f"{device_tracker['jtag_index']:10d}   "
        f"{device_tracker['family']:15s} "
        f"{device_tracker['dna']:<30d}"
    )
    device.program(file)
    print()


@click.command(name="json_devices")
def json_devices():
    # click command string above is required because of underscore in name
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    scanner = DeviceScanner(session.hw_server, session.cs_server)
    print(scanner)


class TreePrinter(NodeVisitorBase):
    tree_glyphs_std = {"blank": "    ", "line": "│   ", "middle": "├── ", "last": "└── "}
    tree_glyphs_alt = {"blank": "    ", "line": "|   ", "middle": "|-- ", "last": "\\-- "}
    tree_glyphs_space = {"blank": "    ", "line": "    ", "middle": "    ", "last": "    "}
    tree_glyphs_none = {"blank": "", "line": "", "middle": "", "last": ""}
    tree_glyphs_selector = {
        "std": tree_glyphs_std,
        "alt": tree_glyphs_alt,
        "space": tree_glyphs_space,
        "none": tree_glyphs_none,
    }

    def __init__(self, session, view_name):
        self._tree_glyphs = TreePrinter.tree_glyphs_std
        self._show_context = True
        self._jtag_index = None
        self.session = session
        self._view_name = view_name
        self._indent_prefix = list()

        if view_name == "chipscope":
            view = self.session.cs_server.get_view(view_name)
        else:
            view = self.session.hw_server.get_view(view_name)
        super().__init__(view)

    def print(self, *, show_context=False, glyph_type="std"):
        self._tree_glyphs = TreePrinter.tree_glyphs_selector.get(glyph_type)
        self._jtag_index = None
        self._show_context = show_context
        print(self._view_name)
        self._indent_prefix = list()
        self.walk()

    # def _print_node_properties(self, node):
    #     props_dict = node.props
    #     for key, val in props_dict.items():
    #         if key != "regs":
    #             print(f"        {key:}: {val}")
    #     # Special printing for all regs - they need to be refreshed
    #     regs = node.props.get("regs")
    #     if regs:
    #         reg_names_to_refresh = tuple(regs.keys())
    #         node.update_regs(reg_names=reg_names_to_refresh, force=True, done=None)
    #         for reg_key, reg_val in regs.items():
    #             bytearray_data = reg_val.data
    #             int_value = int.from_bytes(bytearray_data, byteorder="little", signed=False)
    #             print(f"        regs.{reg_key:}: {hex(int_value)}")

    def _print_node(self, node, prefix):
        name = node.props.get("Name")
        cls = node.props.get("node_cls")
        # Example: <class \'chipscopy.client.jtagdevice.JtagCable\'>
        match = re.fullmatch("^<class \\'(.+)\\'>$", str(cls))
        full_class_name = match.group(1)
        class_name = full_class_name.split(".")[-1]
        node_str = f"{prefix}{name} ({class_name})"
        if self._show_context:
            indent_character_count = 50 - len(node_str)
            if indent_character_count < 0:
                indent_character_count = 2
            indent = " " * indent_character_count
            print(f"{node_str}{indent}{node.ctx}")
        else:
            print(f"{node_str}")

    def _visit_JtagCable(self, node, is_last_sibling):
        # Tracking JtagCable and JtagDevice so we can keep running jtag_index per device in the chain
        self._jtag_index = 0
        self._visit_default(node, is_last_sibling)

    def _visit_JtagDevice(self, node, is_last_sibling):
        # Tracking JtagCable and JtagDevice so we can keep running jtag_index per device in the chain
        self._jtag_index += 1
        self._visit_default(node, is_last_sibling)

    def _visit_default(self, node, is_last_sibling):
        if is_last_sibling:
            glyph = self._tree_glyphs["last"]
        else:
            glyph = self._tree_glyphs["middle"]
        self._indent_prefix.append(glyph)
        prefix = "".join([i for i in self._indent_prefix])
        self._print_node(node, prefix)
        children = list(self._view.get_children(node))
        # Need to update prefix glyphs before moving to next nodes
        for idx, item in enumerate(self._indent_prefix):
            if item == self._tree_glyphs["last"]:
                self._indent_prefix[idx] = self._tree_glyphs["blank"]
            elif item == self._tree_glyphs["middle"]:
                self._indent_prefix[idx] = self._tree_glyphs["line"]
        self.walk(children)
        self._indent_prefix.pop()


@click.command()
@click.option(
    "--view", default="jtag", required=False, help="Use the specified view for walking nodes"
)
@click.option(
    "--show-context", is_flag=True, default=False, required=False, help="Print node context"
)
@click.option("--glyph-type", default="std", required=False, help="Tree glyph type")
def tree(view, show_context, glyph_type):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    tree_printer = TreePrinter(session, view)
    tree_printer.print(show_context=show_context, glyph_type=glyph_type)


def main():
    _chipscopy.add_command(tree)
    _chipscopy.add_command(program)
    _chipscopy.add_command(ls)
    _chipscopy.add_command(info)
    _chipscopy.add_command(json_devices)
    _chipscopy.add_command(report)
    _chipscopy()


if __name__ == "__main__":
    main()
