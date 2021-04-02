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
from typing import ClassVar, TYPE_CHECKING
from dataclasses import dataclass

from chipscopy.utils.printer import printer
from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore

if TYPE_CHECKING:
    from chipscopy.client.axis_pcie_core_client import AxisPCIeCoreClient


@dataclass
class PCIe(DebugCore["AxisPCIeCoreClient"]):
    def __init__(self, pcie_tcf):
        super(PCIe, self).__init__(CoreType.AXIS_PCIE, pcie_tcf)

        self.name = pcie_tcf.props["Name"]
        self.uuid = self.core_info.uuid

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "uuid": self.uuid}

    def get_property(self, property_name_list=None):
        return_dict = {}
        items = self.get_properties()
        if (property_name_list is None) or (len(property_name_list) == 0):
            return_dict = items
        else:
            for key in property_name_list:
                if key in items:
                    return_dict[key] = items[key]
        return return_dict

    def get_properties(self):
        items = {"name": self.name, "uuid": self.uuid}
        items.update(self.core_tcf_node.props)
        return items

    def refresh(self):
        """
        Reads the PCIe debug memory again, and updated internal properties.

        Args:
            None

        Returns:
            None

        """
        self.core_tcf_node.read_data()
        self.get_property([])

    def read_data(self):
        """
        Reads the PCIe debug memory again, and updated internal properties, same as refresh()

        Args:
            None

        Returns:
            None

        """
        self.core_tcf_node.read_data()
        self.get_property([])

    def reset_core(self):
        """
        Resets the PCIe debug core, telling the IP to start collecting a new state trace

        Args:
            None

        Returns:
            None

        """
        self.core_tcf_node.reset_core()

    def __str__(self):
        return f"PCIe {self.name} ({self.uuid})"

    @staticmethod
    def _cap(s):
        return ".".join(i.capitalize() for i in s.split("."))

    def get_dot(self):
        """
        Returns a text string of the PCIe LTSSM in the DOT format. DOT is a graph
        description language:
        (https://en.wikipedia.org/wiki/DOT_(graph_description_language))
        This format can be graphed using python (networkx) or other graphing tools (graphviz
        and others)

        Args:
            None

        Returns:
            String with the PCIe LTSSM graph in a DOT format, using the same colors and labels
            as get_plt()

        """
        pos = {
            "Detect": 'pos="2,0!"',
            "Polling": 'pos="2,-2!"',
            "Configuration": 'pos="2,-4!"',
            "L0": 'pos="2,-6!"',
            "L1": 'pos="1,-7!"',
            "L0s": 'pos="2,-8!"',
            "R.Lock": 'pos="4,-8!"',
            "R.Speed": 'pos="4,-10!"',
            "R.Cfg": 'pos="6,-8!"',
            "R.Idle": 'pos="8,-8!"',
            "R.Eq": 'pos="6,-10!"',
            "Loopback": 'pos="4.5,-5.5!"',
            "Hotreset": 'pos="4.5,-4!"',
            "Disabled": 'pos="4.5,-2!"',
        }

        dot_src = "digraph {\n"
        dot_src += 'graph [pad="0.212,0.055" bgcolor=white splines=true esep="+40" sep="+50"]\n'
        dot_src += "node [style=filled]\n"
        d = self.get_property([])
        val_map = {}
        for state in pos.keys():
            s = "state." + state.replace(" ", "").lower()
            val_map[state] = "orange" if d[s] == 2 else "green" if d[s] == 1 else "gray"
            dot_src += f'"{state}" [fillcolor="{val_map[state]}" {pos[state]}]\n'

        for key in d.keys():
            if key.startswith("edge."):
                value = d[key]
                p = re.compile("edge.(.+)_(.+)")
                m = p.match(key)
                start = PCIe._cap(m.group(1))
                end = PCIe._cap(m.group(2))
                dot_src += f'  {start} -> {end} [label = "{value}"]\n'
        dot_src += "}"
        return dot_src

    def print_trace(self):
        """
        Prints PCIe trace to console, parsing the hierarchy of loops and substates to create
        a user-friendly output

        Args:
            None

        Returns:
            None

        """
        key, trace = self.property.get("state.trace").popitem()
        for t in trace:
            PCIe.print_bracketed(t, 0)

    @staticmethod
    def print_bracketed(trace, indent):
        colors = ["green", "blue", "magenta", "yellow", "blue"]
        color = colors[indent]
        if str(trace).isdigit():
            p = "\t" * indent + f"[{color}]{trace}[/{color}]"
            printer(p)
            return 0
        brace_locations = PCIe.find_brace(trace, "[]")
        start = str(trace).find("[")
        prev = 0
        end = -1
        while start != -1:

            end = brace_locations[start]
            items = trace[prev:start].split(",")
            for item in items:
                if item != "":
                    p = "\t" * indent + f"[{color}]{str(item).strip()}[/{color}]"
                    printer(p)
            PCIe.print_bracketed(trace[start + 1 : end], indent + 1)
            # skip past the ending bracket and comma
            prev = end + 1
            if prev >= len(trace):
                return
            if trace[prev] == ",":
                prev = prev + 1
            start = trace.find("[", prev + 1)
        else:
            items = str(trace[end + 1 :]).split(",")
            for item in items:
                if item != "":
                    p = "\t" * indent + f"[{color}]{str(item).strip()}[/{color}]"
                    printer(p)
        return 0

    @staticmethod
    def find_brace(s, braces):
        toret = {}
        pstack = []

        for i, c in enumerate(s):
            if c == braces[0]:
                pstack.append(i)
            elif c == braces[1]:
                if len(pstack) == 0:
                    raise IndexError("No matching closing parens at: " + str(i))
                toret[pstack.pop()] = i

        if len(pstack) > 0:
            raise IndexError("No matching opening parens at: " + str(pstack.pop()))

        return toret

    def get_plt(self):
        """
        Returns a matplotlib figure to plot, showing the PCIe LTSSM graph.  States will be
        colored green if they have been visited, orange if it's the last state visited, and
        grey if not visited.  The edge labels represent the number of times that state
        transition has be traversed.

        Args:
            None

        Returns:
            A matplotlib.pyplot that can be titled and shown later (can use plt.title
            or plt.show()

        """
        import networkx as nx
        import matplotlib.pyplot as plt

        d = self.get_property([])

        graph = nx.MultiDiGraph()
        graph.add_edges_from(
            [("Detect", "Polling"), ("Polling", "Configuration"), ("Configuration", "L0")],
            label="1",
        )
        graph.add_edges_from(
            [
                ("Polling", "Detect"),
                ("Configuration", "Detect"),
                ("Configuration", "Loopback"),
                ("Configuration", "R.Lock"),
                ("Configuration", "Disabled"),
                ("L0", "L0s"),
                ("L0", "R.Lock"),
                ("L0", "L1"),
                ("L1", "R.Lock"),
                ("L0s", "R.Lock"),
                ("L0s", "L0"),
                ("R.Lock", "Configuration"),
                ("R.Lock", "R.Cfg"),
                ("R.Lock", "R.Eq"),
                ("R.Lock", "Detect"),
                ("R.Cfg", "R.Speed"),
                ("R.Cfg", "R.Idle"),
                ("R.Cfg", "Configuration"),
                ("R.Cfg", "Detect"),
                ("R.Eq", "R.Lock"),
                ("R.Eq", "R.Speed"),
                ("R.Speed", "Detect"),
                #  ("R.Idle", "R.Lock"),
                ("R.Idle", "Loopback"),
                ("R.Idle", "L0"),
                ("R.Idle", "Detect"),
                ("R.Idle", "Hot reset"),
                ("R.Idle", "Disabled"),
                ("Loopback", "Detect"),
                ("Hot reset", "Detect"),
                ("Disabled", "Detect"),
            ],
            weight=2,
            label="999",
        )

        # visual placement of states
        pos = {
            "Detect": [2, 0],
            "Polling": [2, -2],
            "Configuration": [2, -4],
            "L0": [2, -6],
            "L1": [1, -7],
            "L0s": [2, -8],
            "R.Lock": [3, -8],
            "R.Speed": [3, -10],
            "R.Cfg": [4, -8],
            "R.Idle": [5, -8],
            "R.Eq": [4, -10],
            "Loopback": [4, -6],
            "Hot reset": [4, -4],
            "Disabled": [4, -2],
        }
        plt.figure(figsize=(8, 8))
        font = {"color": "k", "fontweight": "bold", "fontsize": 14}
        plt.title("PCIe LTSSM Graph", font)
        val_map = {}
        for state in pos.keys():
            s = "state." + state.replace(" ", "").lower()
            val_map[state] = "orange" if d[s] == 2 else "green" if d[s] == 1 else "gray"

        values = ["grey" if edge not in val_map else val_map[edge] for edge in graph.nodes()]

        # Specify the edges you want here
        blue_edges = [("R.Lock", "R.Cfg"), ("R.Cfg", "R.Idle"), ("R.Idle", "L0")]
        edge_colors = ["black" if edge not in blue_edges else "blue" for edge in graph.edges()]
        edge_labels = {}
        for e in graph.edges():
            prop_name = "edge." + e[0].lower() + "_" + e[1].lower()
            prop_name = prop_name.replace(" ", "")
            val = d[prop_name]
            edge_labels[e] = val
        nx.draw_networkx_nodes(graph, pos, node_color=values, node_size=1500)

        nx.draw_networkx_labels(graph, pos)
        nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, arrows=True, arrowsize=10)
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
        return plt
