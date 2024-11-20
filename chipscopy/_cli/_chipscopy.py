# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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
#
import re
from collections import deque
import argparse
import sys
import os
from pathlib import Path
from typing import Tuple, Dict, Union

from more_itertools import one

import chipscopy
from chipscopy import create_session, report_versions, report_devices
from chipscopy.api.session import Session
from chipscopy.client.view_info import ViewInfo
from chipscopy.dm import Node


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
        return visitor_method(upgraded_node, is_last_sibling)  # noqa

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
_bypass_version_check: bool = True


def display_banner():
    print(f"\n******** Xilinx ChipScoPy v{chipscopy.__version__}")
    print("  ****** Copyright (C) 2021-2022 Xilinx, Inc. All Rights Reserved.\n")
    print("  ****** Copyright (C) 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.\n")
    print("WARNING: Commands and options are subject to change.")
    print()


def report(session: Session, *, devices: bool = True, servers: bool = True):
    if servers:
        report_versions(session)
    if devices:
        report_devices(session)


def _get_node_path(host: str, view: ViewInfo, view_name: str, node: Node) -> str:
    name = node.props.get("Name", "")
    path = ""
    if name:
        hier_name = ""
        parent_ctx = node.parent_ctx
        while parent_ctx:
            parent = view.get_node(parent_ctx)
            hier_name = f"{hier_name}{parent.props.get('Name')}/"
            parent_ctx = parent.parent_ctx
        path = f"{host}/{view_name}/{hier_name}{name}"
    return path


def _get_all_nodes(session: Session) -> Dict[Tuple[str, str], Tuple[int, str, ViewInfo, Node]]:
    retval = {}
    views = ["jtag", "memory", "debugcore", "chipscope"]
    index = 0
    for view_name in views:
        if view_name == "chipscope" and session.cs_server:
            host = session.cs_server.props.get("url")
            view = session.cs_server.get_view(view_name)
            if not view:
                # Not an error for no cs_server - just ignore
                continue
        elif session.hw_server:
            host = session.hw_server.props.get("url")
            view = session.hw_server.get_view(view_name)
        else:
            raise RuntimeError(f"Unable to get view {view_name} from server")
        # Do a depth first search - neater results for numbering (don't use view.get_all())
        node_list = deque(view.get_children())
        while node_list:
            node = node_list.popleft()
            if node.props.get("Name"):
                retval[(view_name, node.ctx)] = (index, host, view, node)
                index += 1
            children = list(view.get_children(node))
            children.reverse()
            node_list.extendleft(children)
    return retval


def program(
    session: Session,
    *,
    file: Union[str, Path] = "",
    dna: str = "",
    cable_context: str = "",
    context: str = "",
    part: str = "",
    family: str = "",
    jtag_index: str = "",
    device_index: str = "",
    skip_reset: bool = False,
    list_: bool = False,
    program_log: bool = False,
    force_reset: bool = False,
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

    if not file and not program_log and not force_reset:
        raise RuntimeError("No programming file specified.")

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

    if force_reset:
        print("Resetting Device", end="")
        print_device(device)
        device.reset()
        print()

    if file:
        print("Programming:", end="")
        print_device(device)
        device.program(file, skip_reset=skip_reset)
        print()

    if program_log:
        print()
        print(device.get_program_log())
        print()


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

    def __init__(self, session, view_name, print_properties):
        self._tree_glyphs = TreePrinter.tree_glyphs_std
        self._show_context = True
        self._jtag_index = None
        self.session = session
        self._view_name = view_name
        self._indent_prefix = list()
        self._print_properties = print_properties
        self._all_nodes = _get_all_nodes(self.session)

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

    def _print_node_properties(self, node: Node, node_str: str, prefix: str):
        props_dict = node.props
        prop_prefix = " " * len(prefix)
        for key, val in props_dict.items():
            if key != "regs":
                print(f"{prop_prefix}    {key:}: {val}")
        # Special printing for all regs - they need to be refreshed
        regs = node.props.get("regs")
        if regs:
            reg_names_to_refresh = tuple(regs.keys())
            node.update_regs(reg_names=reg_names_to_refresh, force=True, done=None)
            for reg_key, reg_val in regs.items():
                reg_data_len = len(reg_val.data)
                for index in range(0, reg_data_len):
                    int_value = int.from_bytes(
                        reg_val.data[index], byteorder="little", signed=False
                    )
                    if reg_data_len == 1:
                        print(f"{prop_prefix}    regs.{reg_key:}: {hex(int_value)}")
                    else:
                        print(f"{prop_prefix}    regs.{reg_key:}.slr{index}: {hex(int_value)}")

    def _print_node(self, node: Node, prefix: str):
        name = node.props.get("Name")
        cls = node.props.get("node_cls")
        # Example: <class \'chipscopy.client.jtagdevice.JtagCable\'>
        match = re.fullmatch("^<class \\'(.+)\\'>$", str(cls))
        full_class_name = match.group(1)
        class_name = full_class_name.split(".")[-1]

        found_val = self._all_nodes.get((self._view_name, node.ctx))

        try:
            # index:int, ctx:str, view:ViewInfo, node:Node
            (index, _, _, _) = self._all_nodes[(self._view_name, node.ctx)]
        except KeyError as ex:
            index = "?"
        node_str = f"{prefix}{index}- {name} ({class_name})"
        if self._show_context:
            indent_character_count = 50 - len(node_str)
            if indent_character_count < 0:
                indent_character_count = 2
            indent = " " * indent_character_count
            print(f"{node_str}{indent}{node.ctx}")
        else:
            print(f"{node_str}")
        if self._print_properties:
            self._print_node_properties(node, node_str, prefix)

    def _visit_JtagCable(self, node: Node, is_last_sibling: bool):
        # Tracking JtagCable and JtagDevice so we can keep running jtag_index per device in the chain
        self._jtag_index = 0
        self._visit_default(node, is_last_sibling)

    def _visit_JtagDevice(self, node: Node, is_last_sibling: bool):
        # Tracking JtagCable and JtagDevice so we can keep running jtag_index per device in the chain
        self._jtag_index += 1
        self._visit_default(node, is_last_sibling)

    def _visit_default(self, node: Node, is_last_sibling: bool):
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


def tree(
    session: Session, *, view=None, show_context=True, glyph_type="std", print_properties=False
):
    if isinstance(view, str):
        views = [view]
    elif isinstance(view, list):
        views = view
    else:
        views = ["jtag", "memory", "debugcore", "chipscope"]

    for view in views:
        tree_printer = TreePrinter(session, view, print_properties)
        tree_printer.print(show_context=show_context, glyph_type=glyph_type)
        print()


def ls(session: Session, *, is_long: bool = False, show_context: bool = False):
    all_nodes = _get_all_nodes(session)
    for (view_name, ctx), (index, host, view, node) in all_nodes.items():
        print(f"{index}  ", end="")
        if is_long:
            path = _get_node_path(host, view, view_name, node)
            print(f"{path}", end="")
        else:
            print(f"{node.props.get('Name')}", end="")

        if show_context:
            print(f"    {node.ctx}")
        else:
            print()


def _print_info(*, host: str, view_name: str, view: ViewInfo, node: Node):
    if not node.props.get("Name"):
        return

    print("ctx:", node.ctx)
    print("host:", host)
    print("view:", view_name)
    path = _get_node_path(host, view, view_name, node)
    print("path:", path)

    props_dict = node.props
    for key, val in props_dict.items():
        if key != "regs":
            print(f"{key}: {val}")
    # Special printing for all regs - they need to be refreshed
    regs = node.props.get("regs")
    if regs:
        reg_names_to_refresh = tuple(regs.keys())
        node.update_regs(reg_names=reg_names_to_refresh, force=True, done=None)
        for reg_key, reg_val in regs.items():
            reg_data_len = len(reg_val.data)
            for index in range(0, reg_data_len):
                int_value = int.from_bytes(reg_val.data[index], byteorder="little", signed=False)
                if reg_data_len == 1:
                    print(f"regs.{reg_key:}: {hex(int_value)}")
                else:
                    print(f"regs.{reg_key:}.slr{index}: {hex(int_value)}")


def info(session: Session, *, match_string: str):
    all_nodes = _get_all_nodes(session)
    try:
        match_string_int_value = int(match_string)
    except ValueError:
        match_string_int_value = -1

    for (view_name, ctx), (index, host, view, node) in all_nodes.items():
        if node.ctx == match_string or index == match_string_int_value:
            _print_info(host=host, view_name=view_name, view=view, node=node)
            break


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
        "--show-context", required=False, action="store_true", help="Print additional node context"
    )
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
    program_parser.add_argument("--force-reset", action="store_true", help="reset device")

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
    tree_parser.add_argument(
        "--properties",
        action="store_true",
        help="Show properties for nodes",
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
        with create_session(
            hw_server_url=_hw_url, cs_server_url=_cs_url, bypass_version_check=_bypass_version_check
        ) as session:
            report(session=session, devices=args.devices, servers=args.servers)

    elif args.subcommand == "info":
        with create_session(
            hw_server_url=_hw_url,
            cs_server_url=_cs_url,
            initial_device_scan=False,
            bypass_version_check=_bypass_version_check,
        ) as session:
            info(session=session, match_string=args.context)

    elif args.subcommand == "ls":
        with create_session(
            hw_server_url=_hw_url,
            cs_server_url=_cs_url,
            initial_device_scan=False,
            bypass_version_check=_bypass_version_check,
        ) as session:
            ls(session=session, is_long=args.long, show_context=args.show_context)

    elif args.subcommand == "program":
        with create_session(
            hw_server_url=_hw_url, cs_server_url=_cs_url, bypass_version_check=_bypass_version_check
        ) as session:
            program(
                session=session,
                file=args.file,
                dna=args.dna,
                cable_context=args.cable_context,
                context=args.context,
                part=args.part,
                family=args.family,
                jtag_index=args.jtag_index,
                device_index=args.device_index,
                skip_reset=args.skip_reset,
                list_=args.list_,
                program_log=args.program_log,
                force_reset=args.force_reset,
            )

    elif args.subcommand == "tree":
        with create_session(
            hw_server_url=_hw_url,
            cs_server_url=_cs_url,
            initial_device_scan=False,
            bypass_version_check=_bypass_version_check,
        ) as session:
            tree(
                session=session,
                view=args.view,
                show_context=args.show_context,
                glyph_type=args.glyph_type,
                print_properties=args.properties,
            )


def main():  # pragma: no cover
    parse_args(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    main()
