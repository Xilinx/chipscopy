# Copyright (C) 2025, Advanced Micro Devices, Inc.
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
from typing import Callable, Sequence
from dataclasses import dataclass, asdict, field
from typing import Generator, Dict, List, Union, Optional, Sequence, Any


class Rule:
    def __init__(
        self, name: str, predicate: Callable[["ProbeDataMapper", int], bool], signals: Sequence[str]
    ):
        """
        name      – the label shown when this rule fires
        predicate – function(pd, idx) → bool
        signals   – list of probe names this rule reads
        """
        self.name = name
        self._predicate = predicate
        self.signals = list(signals)

    def applies(self, pd: "ProbeDataMapper", idx: int) -> bool:
        return self._predicate(pd, idx)

    @classmethod
    def rising_edge(cls, name: str, signal: str):
        """Fire on a 0→1 edge of `signal`."""
        return cls(name, lambda pd, i: pd.rising_edge(signal, i), signals=[signal])

    @classmethod
    def all_asserted(cls, name: str, *signals: str):
        """Fire when both sig1 & sig2 are high."""

        def predicate(pd, idx):
            return all(pd.signal(sig, idx) == 1 for sig in signals)

        return cls(name, predicate, signals=list(signals))


# AXI4-Lite rules: single-beat reads/writes (no bursts, no IDs, no *LAST)
axi_lite_rules = [
    # Read Address
    Rule.rising_edge("Read-Address-Init", "arvalid"),
    Rule.all_asserted("Read-Address-End", "arvalid", "arready"),
    # Read Data (single beat; completion of a read)
    Rule(
        "Read-Data",
        lambda pd, i: pd.both_asserted("rvalid", "rready", i),
        signals=["rvalid", "rready"],
    ),
    # Write Address
    Rule.rising_edge("Write-Address-Init", "awvalid"),
    Rule.all_asserted("Write-Address-End", "awvalid", "awready"),
    # Write Data (single beat; no WLAST in AXI4-Lite)
    Rule(
        "Write-Data",
        lambda pd, i: pd.both_asserted("wvalid", "wready", i),
        signals=["wvalid", "wready"],
    ),
    # Write Response (single beat; completion of a write)
    Rule.all_asserted("Write-Response", "bvalid", "bready"),
]


axi_STRMrules = [
    # Basic handshake on AXI4-Stream
    Rule.all_asserted("Stream-Beat", "tvalid", "tready"),
    # Last beat of a packet (TLAST asserted with a valid handshake)
    Rule(
        "Stream-Last",
        lambda pd, i: pd.both_asserted("tvalid", "tready", i) and pd.signal("tlast", i) == 1,
        signals=["tvalid", "tready", "tlast"],
    ),
]
axi_MMrules = [
    Rule.rising_edge("Read-Address-Init", "arvalid"),
    Rule.all_asserted("Read-Address-End", "arvalid", "arready"),
    # Read-Data Channel
    Rule(
        "Read-Data-Beat",
        lambda pd, i: pd.both_asserted("rvalid", "rready", i) and pd.signal("rlast", i) == 0,
        signals=["rvalid", "rready", "rlast"],
    ),
    Rule(
        "Read-Data-Last",
        lambda pd, i: pd.both_asserted("rvalid", "rready", i) and pd.signal("rlast", i) == 1,
        signals=["rvalid", "rready", "rlast"],
    ),
    # Write-Address Channel
    Rule.rising_edge("Address-Command-Init", "awvalid"),
    Rule.all_asserted("Address-Command", "awvalid", "awready"),
    # Write-Data Channel
    Rule(
        "Data-Beat",
        lambda pd, i: pd.both_asserted("wvalid", "wready", i) and pd.signal("wlast", i) == 0,
        signals=["wvalid", "wready", "wlast"],
    ),
    Rule(
        "Data-Last",
        lambda pd, i: pd.both_asserted("wvalid", "wready", i) and pd.signal("wlast", i) == 1,
        signals=["wvalid", "wready", "wlast"],
    ),
    # Write-Response Channel
    Rule.all_asserted("Write-Response-End", "bvalid", "bready"),
]


@dataclass
class TransactionSpec:
    """
    Simple spec: one open rule and one close rule define a transaction type.
    open_fields and close_fields list the simple signal names you want available
    at open/close (e.g., ["ARID","ARADDR"] and ["RID","RRESP"]).
    """

    name: str  # "Read" or "Write"
    txn_type: str  # "read" | "write"
    open_rule: "Rule"
    close_rule: "Rule"
    # Field names (simple, case-insensitive lookups against waveform signals)
    open_id_field: str  # e.g., "ARID" or "AWID"
    close_id_field: str  # e.g., "RID"  or "BID"
    open_addr_field: str = None  # e.g., "ARADDR" or "AWADDR"
    close_resp_field: str = None
    databeat_rule: Rule = None  # e.g., Rule.all_asserted("Read-Data-Beat", "RVALID", "RREADY")
    open_fields: List[str] = field(default_factory=list)
    close_fields: List[str] = field(default_factory=list)


axi_MM_txn_specs = [
    TransactionSpec(
        name="Read",
        txn_type="read",
        open_rule=Rule.all_asserted("Read-Open", "ARVALID", "ARREADY"),
        close_rule=Rule(
            "Read-Close",
            lambda pd, i: pd.both_asserted("RVALID", "RREADY", i) and pd.signal("RLAST", i) == 1,
            signals=["RVALID", "RREADY", "RLAST"],
        ),
        open_id_field="ARID",
        close_id_field="RID",
        open_addr_field="ARADDR",
        close_resp_field="RRESP",
        # Optional: capture burst metadata into t.meta for tooltips/exports
        #  open_fields=["ARLEN", "ARSIZE", "ARBURST", "ARPROT", "ARQOS"],
        close_fields=["RDATA"],
    ),
    # AXI4-MM: Write opens on AWVALID&AWREADY; closes on BVALID&BREADY
    TransactionSpec(
        name="Write",
        txn_type="write",
        open_rule=Rule.all_asserted("Write-Open", "AWVALID", "AWREADY"),
        close_rule=Rule.all_asserted("Write-Close", "BVALID", "BREADY"),
        open_id_field="AWID",
        close_id_field="BID",
        open_addr_field="AWADDR",
        close_resp_field="BRESP",
        #  open_fields=["AWLEN", "AWSIZE", "AWBURST", "AWPROT", "AWQOS"],
        close_fields=["WDATA"],
    ),
]

axi_lite_txnspecs = [
    TransactionSpec(
        name="AXI-Lite Read",
        txn_type="read",
        # Open when AR handshake completes
        open_rule=Rule.all_asserted("AXIL-Read-Open", "ARVALID", "ARREADY"),
        # Close when R handshake completes (no RLAST in AXI-Lite)
        close_rule=Rule.all_asserted("AXIL-Read-Close", "RVALID", "RREADY"),
        # AXI-Lite has no IDs
        open_id_field=None,
        close_id_field=None,
        open_addr_field="ARADDR",
        close_resp_field="RRESP",
        # Capture read data on close
        close_fields=["RDATA"],
    ),
    TransactionSpec(
        name="AXI-Lite Write",
        txn_type="write",
        # Simplest modeling: open when BOTH AW and W handshakes complete in the same cycle.
        # Note: AXI-Lite allows AW and W to handshake in different cycles; if your traces
        # often stagger them, consider a more advanced open_rule that correlates across cycles.
        open_rule=Rule.all_asserted("AXIL-Write-Open", "AWVALID", "AWREADY", "WVALID", "WREADY"),
        # Close when B handshake completes
        close_rule=Rule.all_asserted("AXIL-Write-Close", "BVALID", "BREADY"),
        open_id_field=None,
        close_id_field=None,
        open_addr_field="AWADDR",
        close_resp_field="BRESP",
        # Capture write data (and optionally strobe) with the transaction
        close_fields=["WDATA"],  # add "WSTRB" if you want byte enables too
    ),
]
