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

import csv
import json
from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from pathlib import Path

from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy.utils.printer import printer

if TYPE_CHECKING:
    from chipscopy.client.pcie_core_client import PCIeCoreClient


@dataclass
class HardenedDebugPCIe(DebugCore["PCIeCoreClient"]):
    """API wrapper for the CPM6 PCIe core.

    Provides access to register properties, LTSSM state trace,
    and graph visualization for  PCIe controllers.
    """

    def __init__(self, pcie_tcf):
        super(HardenedDebugPCIe, self).__init__(CoreType.PCIE, pcie_tcf)
        self.name = pcie_tcf.props.get("Name", "HardenedDebugPCIe")
        self.filter_by = {"name": self.name}

    def get_property(self, property_name_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get values for specified properties, or all if none specified."""
        items = self.get_properties()
        if not property_name_list:
            return items
        return {k: v for k, v in items.items() if k in property_name_list}

    def get_properties(self) -> Dict[str, Any]:
        """Get all properties including name and node props."""
        items: Dict[str, Any] = {"name": self.name}
        items.update(self.core_tcf_node.props)
        return items

    def refresh(self) -> None:
        """Read the LTSSM trace memory and update internal properties."""
        self.core_tcf_node.read_ltssm_trace()
        self.get_property()

    def read_ltssm_trace(self) -> None:
        """Read LTSSM trace memory and update properties. Same as refresh()."""
        self.core_tcf_node.read_ltssm_trace()
        self.get_property()

    def reset_core(self) -> None:
        """Reset the LTSSM trace capture.

        Disables LTSSM feature, zeros trace memory, re-enables capture,
        and clears all cached state/edge/trace properties.
        """
        self.core_tcf_node.reset_core()
        self.get_property()

    def get_trace_data(self) -> List[str]:
        """Returns the raw hex word list from LTSSM trace memory.

        Each entry is a hex string like "0x00012345". Integer entries
        from the server are normalized to hex strings. This is the
        simplest raw dump -- no decoding is performed.
        """
        raw = self.get_properties().get("trace_data", [])
        return [f"0x{e:08x}" if isinstance(e, int) else str(e) for e in raw]

    def get_link_status(self) -> Dict[str, Any]:
        """Returns current link status as a dict.

        Keys: speed, width, ltssm_state, link_info.
        Values are human-readable strings when encoding is available.
        """
        props = self.get_properties()
        return {
            "speed": props.get("LINK_SPEED", "N/A"),
            "width": props.get("LINK_WIDTH", "N/A"),
            "ltssm_state": props.get("LTSSM_STATE", "N/A"),
            "link_info": props.get("link_info", ""),
        }

    def is_link_up(self) -> bool:
        """Returns True if the PCIe link has reached L0 (trained).

        LTSSM_STATE carries the raw state code rather than a name, so it is
        matched against every spelling of L0 the server may report: "0x11"
        from a register alias, "17" if it arrives as a decimal, and "l0" if a
        future encoding resolves it to a name.
        """
        state = self.get_properties().get("LTSSM_STATE", "")
        return str(state).lower() in ("l0", "17", "0x11")

    def get_trace_summary(self) -> Dict[str, Any]:
        """Returns a structured summary of the current trace.

        Keys: entry_count, unique_states, loop_count, current_state, link_info.
        """
        props = self.get_properties()
        trace_data = props.get("trace_data", [])
        state_trace = props.get("state.trace", [])
        loop_count = sum(1 for e in state_trace if isinstance(e, str) and "Loop" in e)

        visited = set()
        for key, val in props.items():
            if key.startswith("state.") and key != "state.trace" and val and val != 0:
                visited.add(key.replace("state.", ""))

        return {
            "entry_count": len(trace_data),
            "unique_states": sorted(visited),
            "loop_count": loop_count,
            "current_state": props.get("LTSSM_STATE", "N/A"),
            "link_info": props.get("link_info", ""),
        }

    def save_trace(self, path: str, fmt: str = "json") -> None:
        """Export trace data to a file.

        Args:
            path: Output file path.
            fmt: Format -- "json" for full decoded trace, "csv" for tabular.
        """
        if fmt == "json":
            data = {
                "trace_data": self.get_trace_data(),
                "decoded": self.get_raw_trace(),
                "summary": self.get_trace_summary(),
            }
            Path(path).write_text(json.dumps(data, indent=2))
        elif fmt == "csv":
            decoded = self.get_raw_trace()
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "raw",
                        "duration_us",
                        "prev_state",
                        "prev_state_code",
                        "curr_state",
                        "curr_state_code",
                        "overflow",
                    ],
                )
                writer.writeheader()
                writer.writerows(decoded)
        else:
            raise ValueError(f"Unsupported format '{fmt}'. Use 'json' or 'csv'.")

    def _ltssm_state_names(self, props: Dict[str, Any]) -> Dict[int, str]:
        """Maps LTSSM state codes to names, empty if the server sends no table.

        The encoding file lives on the server, so the names arrive with the rest
        of the encoding metadata. An `encoding` attribute on the node is still
        honoured for callers that supply a table themselves; older servers send
        no states, and codes are then reported undecoded.
        """
        states = (props.get("ltssm_encoding_meta") or {}).get("states", [])
        if not states:
            node_encoding = getattr(self.core_tcf_node, "encoding", None)
            if node_encoding:
                states = node_encoding.get("states", [])
        names = {}
        for entry in states:
            if "code" in entry and "name" in entry:
                names[entry["code"]] = entry["name"]
        return names

    def get_raw_trace(self) -> List[Dict[str, Any]]:
        """Returns decoded per-word LTSSM trace data including durations.

        Each entry is a dict with keys: raw, duration_us, prev_state,
        prev_state_code, curr_state, curr_state_code, overflow.
        """
        props = self.get_properties()
        trace_data = props.get("trace_data", [])
        if not trace_data:
            return []

        encoding_states = self._ltssm_state_names(props)

        result = []
        for entry in trace_data:
            try:
                if isinstance(entry, int):
                    word = entry
                    raw_str = f"0x{word:08x}"
                else:
                    word = int(str(entry), 0)
                    raw_str = str(entry)
            except (ValueError, TypeError):
                continue

            duration = (word >> 13) & 0xFFFF
            prev_code = (word >> 7) & 0x3F
            curr_code = (word >> 1) & 0x3F
            overflow = word & 0x1

            result.append(
                {
                    "raw": raw_str,
                    "duration_us": duration,
                    "prev_state": encoding_states.get(prev_code, f"unknown({prev_code})"),
                    "prev_state_code": prev_code,
                    "curr_state": encoding_states.get(curr_code, f"unknown({curr_code})"),
                    "curr_state_code": curr_code,
                    "overflow": bool(overflow),
                }
            )
        return result

    # ==================================================================================
    # Visualization (data-driven from server's encoding metadata)
    # ==================================================================================

    @staticmethod
    def _cap(s):
        return ".".join(i.capitalize() for i in s.split("."))

    def _get_encoding_meta(self):
        """Get encoding metadata (edges, graph_positions) from the server."""
        props = self.get_properties()
        return props.get("ltssm_encoding_meta", {})

    def get_dot(self) -> str:
        """Returns the PCIe LTSSM graph in DOT format.

        Graph topology is derived from the server's encoding file.
        States are colored: orange=current, green=visited, gray=unvisited.
        Edge labels show transition counts.
        """
        d = self.get_property()
        meta = self._get_encoding_meta()
        graph_positions = meta.get("graph_positions", {})
        edges = meta.get("edges", [])

        dot_src = "digraph {\n"
        dot_src += 'graph [pad="0.212,0.055" bgcolor=white splines=true esep="+40" sep="+50"]\n'
        dot_src += "node [style=filled]\n"

        for macro_state, xy in graph_positions.items():
            cap_name = self._cap(macro_state)
            state_key = f"state.{macro_state}"
            val = d.get(state_key, 0)
            color = "orange" if val == 2 else "green" if val == 1 else "gray"
            pos_str = f'pos="{xy[0]},{xy[1]}!"'
            dot_src += f'"{cap_name}" [fillcolor="{color}" {pos_str}]\n'

        for edge_name in edges:
            parts = edge_name.split("_", 1)
            if len(parts) == 2:
                start = self._cap(parts[0])
                end = self._cap(parts[1])
                count = d.get(f"edge.{edge_name}", 0)
                dot_src += f'  "{start}" -> "{end}" [label = "{count}"]\n'

        dot_src += "}"
        return dot_src

    def get_plt(self):
        """Renders the CPM6 Hardened Debug PCIe LTSSM graph as a matplotlib figure.

        State node colors mirror the soft AXIS-PCIe convention:
          - **orange**  – most-recently seen state (end of captured trace)
          - **green**   – visited at least once during the trace
          - **gray**    – not visited

        The PCIe recovery path (L0→R.Lock→R.Cfg→R.Idle→L0, and the Gen3
        equalization sub-path R.Lock→R.Eq→R.Speed→R.Lock) is drawn in **blue**
        so the hot path stands out at a glance — matching the blue-edge convention
        used by the soft AXIS-PCIe ``get_plt()``.  All other edges are black.

        Visited edges are drawn thicker; unvisited edges are drawn thinner and
        lighter.  Edge-transition counts appear as labels on each arrow; zero
        counts are suppressed for readability.  A legend and the detected link
        speed/width are included in the figure.

        Returns the ``matplotlib.pyplot`` module so the caller can do::

            plt = pcie.get_plt()
            plt.show()
            # or: plt.savefig("ltssm.png", dpi=150, bbox_inches="tight")
        """
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        d = self.get_property()
        meta = self._get_encoding_meta()
        graph_positions = meta.get("graph_positions", {})
        edges = meta.get("edges", [])

        graph = nx.MultiDiGraph()

        # Build position map — capitalize node labels ("r.lock" → "R.Lock")
        pos = {}
        for macro_state, xy in graph_positions.items():
            cap_name = self._cap(macro_state)
            pos[cap_name] = xy

        # Add edges to the graph
        for edge_name in edges:
            parts = edge_name.split("_", 1)
            if len(parts) == 2:
                src = self._cap(parts[0])
                dst = self._cap(parts[1])
                graph.add_edge(src, dst)

        # ------------------------------------------------------------------
        # Figure & axes
        # ------------------------------------------------------------------
        link_info = d.get("link_info", "")
        title = "Hardened Debug PCIe LTSSM Graph"
        if link_info:
            title = f"Hardened Debug PCIe LTSSM Graph  [{link_info}]"

        fig, ax = plt.subplots(figsize=(12, 9))
        ax.set_title(title, fontsize=14, fontweight="bold", color="k", pad=12)
        ax.axis("off")

        # ------------------------------------------------------------------
        # Node colors: orange = current/last, green = visited, gray = not visited
        # ------------------------------------------------------------------
        _C_CURRENT = "#FF8C00"  # dark orange  (state flag == 2)
        _C_VISITED = "#2ECC71"  # medium green (state flag == 1)
        _C_UNVISITED = "#BDBDBD"  # light gray   (state flag == 0 / missing)

        val_map = {}
        for macro_state in graph_positions:
            cap_name = self._cap(macro_state)
            val = d.get(f"state.{macro_state}", 0)
            val_map[cap_name] = _C_CURRENT if val == 2 else _C_VISITED if val == 1 else _C_UNVISITED

        node_colors = [val_map.get(n, _C_UNVISITED) for n in graph.nodes()]

        # ------------------------------------------------------------------
        # Edge colors & widths
        # Recovery path → blue (bright=visited, pale=unvisited)
        # All other edges  → black (dark=visited, light gray=unvisited)
        # ------------------------------------------------------------------
        # The recovery "hot path" edges — mirrors soft PCIe blue convention
        _RECOVERY_EDGES = {
            ("L0", "R.Lock"),  # entry into recovery
            ("R.Lock", "R.Cfg"),  # main recovery forward
            ("R.Lock", "R.Eq"),  # Gen3 equalization entry
            ("R.Lock", "R.Speed"),  # direct speed-change shortcut
            ("R.Eq", "R.Speed"),  # EQ → speed negotiation
            ("R.Speed", "R.Lock"),  # loop back after speed change
            ("R.Cfg", "R.Idle"),  # recovery continuation
            ("R.Idle", "L0"),  # recovery complete → trained L0
        }

        edge_list = list(graph.edges())
        edge_colors = []
        edge_widths = []
        for src, dst in edge_list:
            count = d.get(f"edge.{src.lower()}_{dst.lower()}", 0)
            in_recovery = (src, dst) in _RECOVERY_EDGES
            if in_recovery:
                edge_colors.append("#1565C0" if count else "#90CAF9")  # dark / pale blue
            else:
                edge_colors.append("#1A1A1A" if count else "#C0C0C0")  # dark / light gray
            edge_widths.append(2.5 if count else 1.0)

        # Edge labels — show transition counts, suppress zeros
        edge_labels = {}
        for src, dst in graph.edges():
            count = d.get(f"edge.{src.lower()}_{dst.lower()}", 0)
            if count:
                edge_labels[(src, dst)] = str(count)

        # ------------------------------------------------------------------
        # Draw
        # ------------------------------------------------------------------
        nx.draw_networkx_nodes(
            graph,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=2000,
            edgecolors="black",
            linewidths=1.5,
        )
        nx.draw_networkx_labels(
            graph,
            pos,
            ax=ax,
            font_size=9,
            font_weight="bold",
        )
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edge_color=edge_colors,
            width=edge_widths,
            arrows=True,
            arrowsize=15,
            node_size=2000,  # must match above so arrows land on node boundary
        )
        if edge_labels:
            nx.draw_networkx_edge_labels(
                graph,
                pos,
                ax=ax,
                edge_labels=edge_labels,
                font_size=8,
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.75},
            )

        # ------------------------------------------------------------------
        # Legend
        # ------------------------------------------------------------------
        legend_handles = [
            mpatches.Patch(facecolor=_C_CURRENT, edgecolor="black", label="Current / last state"),
            mpatches.Patch(facecolor=_C_VISITED, edgecolor="black", label="Visited"),
            mpatches.Patch(facecolor=_C_UNVISITED, edgecolor="black", label="Not visited"),
            mpatches.Patch(
                facecolor="#90CAF9", edgecolor="none", label="Recovery path (not taken)"
            ),
            mpatches.Patch(facecolor="#1565C0", edgecolor="none", label="Recovery path (taken)"),
        ]
        ax.legend(handles=legend_handles, loc="upper right", fontsize=8, framealpha=0.85)

        fig.tight_layout()
        return plt

    def print_trace(self) -> None:
        """Prints the LTSSM state trace to console with formatted output."""
        props = self.get_properties()
        trace = props.get("state.trace", [])
        for t in trace:
            self._print_bracketed(t, 0)

    @staticmethod
    def _print_bracketed(trace, indent):
        colors = ["green", "blue", "magenta", "yellow", "blue"]
        color = colors[indent % len(colors)]
        if str(trace).isdigit():
            printer("\t" * indent + f"[{color}]{trace}[/{color}]")
            return
        brace_locations = HardenedDebugPCIe._find_brace(trace, "[]")
        start = str(trace).find("[")
        prev = 0
        end = -1
        while start != -1:
            end = brace_locations[start]
            items = trace[prev:start].split(",")
            for item in items:
                if item != "":
                    printer("\t" * indent + f"[{color}]{str(item).strip()}[/{color}]")
            HardenedDebugPCIe._print_bracketed(trace[start + 1 : end], indent + 1)
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
                    printer("\t" * indent + f"[{color}]{str(item).strip()}[/{color}]")

    @staticmethod
    def _find_brace(s, braces):
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

    def __str__(self):
        return f"HardenedDebugPCIe {self.name}"
