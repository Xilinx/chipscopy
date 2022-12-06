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
from operator import itemgetter
import argparse
import sys
import os

from more_itertools import one

import chipscopy
from chipscopy.api.device.device_scanner import create_device_scanner
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
_hw_url: str = os.getenv("HW_SERVER_URL", "localhost:3121")
_cs_url: str = os.getenv("CS_SERVER_URL", "localhost:3042")


def display_banner():
    print(f"\n******** Xilinx ChipScoPy v{chipscopy.__version__}")
    print("  ****** Copyright 2021-2022 Xilinx, Inc. All Rights Reserved.\n")
    print("WARNING: Commands and options are subject to change.")
    print()


def report(devices, servers):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    if devices:
        report_devices(session)
    elif servers:
        report_versions(session)
    else:
        report_versions(session)
        report_devices(session)


def _create_path(device_count, hier_name):
    return f"/device/{device_count}/{hier_name}"


def info(match_string):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    device_list = session.devices
    device_count = 0
    for device in device_list:
        d = device.to_dict()
        for node_dict in d.get("node_identification", []):
            server_type, view_name, name, context, hier_name = itemgetter(
                "server_type", "view_name", "name", "context", "hier_name"
            )(node_dict)
            path = _create_path(device_count, hier_name)
            if path == match_string or context == match_string:
                print("target      :", path)
                print("server_type :", server_type)
                print("view        :", view_name)
                print("part        :", d.get("part"))
                print("context     :", d.get("context"))
                print("dna         :", hex(d.get("dna")) if d.get("dna") else None)
                print("cable       :", d.get("cable_context"))
                print("jtag_index  :", d.get("jtag_index"))
            device_count += 1


def ls(is_long):
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    device_list = session.devices
    device_count = 0
    for device in device_list:
        d = device.to_dict()
        for node_dict in d.get("node_identification", []):
            server_type, view_name, name, context, hier_name = itemgetter(
                "server_type", "view_name", "name", "context", "hier_name"
            )(node_dict)
            path = _create_path(device_count, hier_name)
            if is_long:
                print(f"{path:60s} {context}")
            else:
                print(f"{path}")
        device_count += 1


def program(
    file,
    dna,
    cable_context,
    context,
    part,
    family,
    jtag_index,
    device_index,
    skip_reset,
    list_,
    program_log,
):
    def print_device(device_):
        d = device_.to_dict()
        keys = ["jtag_index", "part", "dna", "context", "cable_context"]
        for key in keys:
            if key == "dna" and d.get(key):
                val = hex(d.get(key))
            else:
                val = d.get(key)
            print(f"  {key}:{val}", end="")
        print()

    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    all_devices = session.devices

    args = {}

    if dna:
        args["dna"] = int(dna, 0)
    if context:
        args["context"] = context
    if cable_context:
        args["cable_context"] = cable_context
    if context:
        args["context"] = context
    if part:
        args["part"] = part
    if family:
        args["family"] = family
    if jtag_index:
        args["jtag_index"] = int(jtag_index)

    if list_:
        if len(args) > 0:
            raise ValueError("--list is not allowed with other options")
        for idx, device in enumerate(all_devices):
            print(f"DEVICE #{idx}:", end="")
            print_device(device)
        return

    if len(all_devices) == 0:
        raise IndexError("No devices in device list")

    if not file and not program_log:
        raise RuntimeError("No progamming file specified.")

    if device_index:
        device_index = int(device_index)
        if len(args) > 0:
            raise ValueError("Device index is not allowed with other options")
        if len(all_devices) <= device_index:
            raise ValueError("Device index out of range")
        device = all_devices[device_index]
    else:
        if len(args) > 0:
            device = all_devices.get(**args)
        elif len(all_devices) == 2 and all_devices[0].to_dict().get("part") == "arm_dap":
            # Ok to ignore arm_dap on same versal
            device = all_devices[1]
        else:
            if len(all_devices) > 1:
                raise ValueError("Multiple devices match selection")
            device = one(all_devices)

    if file:
        print("Programming:", end="")
        print_device(device)
        device.program(file, skip_reset=skip_reset)
        print()

    if program_log:
        print()
        print(device.get_program_log())
        print()


def json_devices():
    # click command string above is required because of underscore in name
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    scanner = create_device_scanner(session.hw_server, session.cs_server)
    print(scanner.to_json())


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


def tree(view, show_context, glyph_type):
    if view:
        views = [view]
    else:
        views = ["jtag", "memory", "debugcore", "chipscope"]
    session = create_session(hw_server_url=_hw_url, cs_server_url=_cs_url)
    for view in views:
        tree_printer = TreePrinter(session, view)
        tree_printer.print(show_context=show_context, glyph_type=glyph_type)
        print()


def parse_args(cmdline_args):
    global _hw_url, _cs_url

    parser = argparse.ArgumentParser(description="ChipScoPy CLI")
    parser.add_argument("-v", "--version", action="store_true", help="Display version")
    parser.add_argument("--no-banner", action="store_true", help="Turn off banner text")
    parser.add_argument("--hw_url", type=str, help="Hardware Server URL")
    parser.add_argument("--cs_url", type=str, help="ChipScope Server URL")

    base_parser = argparse.ArgumentParser(add_help=False)

    subparsers = parser.add_subparsers(help="sub-command", dest="subcommand")

    report_parser = subparsers.add_parser("report", help="report help", parents=[base_parser])
    report_parser.add_argument("--devices", action="store_true", help="Report devices")
    report_parser.add_argument("--servers", action="store_true", help="Report server versions")

    info_parser = subparsers.add_parser("info", help="info help", parents=[base_parser])
    info_parser.add_argument("context", type=str)

    ls_parser = subparsers.add_parser("ls", help="ls help", parents=[base_parser])
    ls_parser.add_argument(
        "--long",
        "-l",
        required=False,
        action="store_true",
        help="long listing including device contexts",
    )

    program_parser = subparsers.add_parser("program", help="program help", parents=[base_parser])
    program_parser.add_argument("file", type=str, nargs="?")
    program_parser.add_argument("--dna", type=str, help="find device to program with dna")
    program_parser.add_argument("--cable-context", type=str, help="jtag cable context")
    program_parser.add_argument("--context", type=str, help="device context")
    program_parser.add_argument("--part", type=str, help="part name")
    program_parser.add_argument("--family", type=str, help="family name")
    program_parser.add_argument(
        "--jtag-index", type=int, help="jtag index in chain (starting index is 0)"
    )
    program_parser.add_argument(
        "--device-index", type=int, help="device index device list (starting index is 0)"
    )
    program_parser.add_argument(
        "--skip-reset", action="store_true", help="Skip the reset before programming device"
    )
    program_parser.add_argument("--list", action="store_true", help="list devices", dest="list_")
    program_parser.add_argument(
        "--program-log", action="store_true", help="download programming log"
    )

    json_parser = subparsers.add_parser(
        "json-devices", help="json-devices help", parents=[base_parser]
    )

    tree_parser = subparsers.add_parser("tree", help="tree help", parents=[base_parser])
    tree_parser.add_argument(
        "--view",
        type=str,
        default=None,
        required=False,
        choices=["jtag", "memory", "debugcore", "chipscope"],
        help="Use the specified view for walking nodes",
    )
    tree_parser.add_argument(
        "--show-context", required=False, action="store_true", help="Print additional node context"
    )
    tree_parser.add_argument(
        "--glyph-type",
        type=str,
        default="std",
        required=False,
        choices=["std", "alt", "space", "none"],
        help="Tree glyph style",
    )

    args = parser.parse_args(cmdline_args)

    if args.version:
        print(chipscopy.__version__)
        sys.exit(0)

    if not args.no_banner:
        display_banner()

    if args.hw_url:
        _hw_url = args.hw_url

    if args.cs_url:
        _cs_url = args.cs_url

    if args.subcommand == "report":
        report(devices=args.devices, servers=args.servers)

    elif args.subcommand == "info":
        info(args.context)

    elif args.subcommand == "ls":
        ls(args.long)

    elif args.subcommand == "program":
        program(
            args.file,
            args.dna,
            args.cable_context,
            args.context,
            args.part,
            args.family,
            args.jtag_index,
            args.device_index,
            args.skip_reset,
            args.list_,
            args.program_log,
        )

    elif args.subcommand == "json-devices":
        json_devices()

    elif args.subcommand == "tree":
        tree(view=args.view, show_context=args.show_context, glyph_type=args.glyph_type)


def main():  # pragma: no cover
    parse_args(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    main()
