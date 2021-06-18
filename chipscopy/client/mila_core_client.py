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

from typing import List, Dict, Tuple, Union, Any
from itertools import islice

from chipscopy import dm
from chipscopy.client import connect_xicom
from chipscopy.client.core_property_client import PropertyValues
from chipscopy.client.core import get_cs_view, CoreParent, CoreClient
from chipscopy.tcf.services import DoneHWCommand, mila
from chipscopy.tcf.services.mila import (
    NAME as MILA_NAME,
    MILAProbeDefs,
    PROP_TRACE_DATA,
    PROP_TRACE_WIDTH,
)


class MILACoreClient(CoreClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "ddrmc_main"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(MILA_NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize(self.ctx, done_cb))

    def terminate(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.terminate(self.ctx, done_cb))

    def write32(self, write_addr: int, data: int, domain_index: int, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.write32(self.ctx, write_addr, data, domain_index, done_cb)
        return self.add_pending(token)

    def read32(
        self, read_addr: int, read_word_count: int, domain_index: int, done: DoneHWCommand = None
    ):
        service, done_cb = self.make_done(done)
        token = service.read32(self.ctx, read_addr, read_word_count, domain_index, done_cb)
        return self.add_pending(token)

    #
    #  Property methods
    #
    def get_property(self, property_names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_property(self.ctx, property_names, done_cb)
        return self.add_pending(token)

    def get_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def report_property(self, property_names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.report_property(self.ctx, property_names, done_cb)
        return self.add_pending(token)

    def report_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.report_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def reset_property(self, property_names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.reset_property(self.ctx, property_names, done_cb)
        return self.add_pending(token)

    def reset_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.reset_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def set_property(self, property_values: PropertyValues, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.set_property(self.ctx, property_values, done_cb)
        return self.add_pending(token)

    def commit_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.commit_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def refresh_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    #
    # Probe Methods
    #
    def define_probe(self, probe_defs: mila.MILAProbeDefs, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.define_probe(self.ctx, probe_defs, done_cb)
        return self.add_pending(token)

    def undefine_probe(self, probe_names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.undefine_probe(self.ctx, probe_names, done_cb)
        return self.add_pending(token)

    def get_probe(self, probe_names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_probe(self.ctx, probe_names, done_cb)
        return self.add_pending(token)

    def get_probe_match_value(self, probe_names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_probe_match_value(self.ctx, probe_names, done_cb)
        return self.add_pending(token)

    def set_probe_match_value(self, match_pairs: Dict[str, str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.set_probe_match_value(self.ctx, match_pairs, done_cb)
        return self.add_pending(token)

    #
    # Core Communication Methods
    #
    def arm(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.arm(self.ctx, done_cb)
        return self.add_pending(token)

    def upload(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.upload(self.ctx, done_cb)
        return self.add_pending(token)

    #
    #  MUX Methods
    #
    def mux_add_node(
        self,
        memory_domain: str,
        addr: Union[int, None],
        name: str,
        long_name: str,
        has_local_inputs: bool = True,
        ch_in0: str = "",
        ch_in1: str = "",
        done: DoneHWCommand = None,
    ):
        service, done_cb = self.make_done(done)
        token = service.mux_add_node(
            self.ctx,
            memory_domain,
            addr,
            name,
            long_name,
            has_local_inputs,
            ch_in0,
            ch_in1,
            done_cb,
        )
        return self.add_pending(token)

    def mux_build_tree(
        self, clk_sel_is_1_mux: str, ila_capture_data_sel_muxes: [str], done: DoneHWCommand = None
    ):
        service, done_cb = self.make_done(done)
        token = service.mux_build_tree(
            self.ctx, clk_sel_is_1_mux, ila_capture_data_sel_muxes, done_cb
        )
        return self.add_pending(token)

    def mux_select_inputs(self, mux_node_inputs, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        # For JSON change tuples into lists.
        mux_node_inputs2 = [None if not item else list(item) for item in mux_node_inputs]
        token = service.mux_select_inputs(self.ctx, mux_node_inputs2, done_cb)
        return self.add_pending(token)

    def mux_get_selected_inputs(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done, restore_tuple=True)
        token = service.mux_get_selected_inputs(self.ctx, done_cb)
        return self.add_pending(token)

    def mux_commit(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.mux_commit(self.ctx, done_cb)
        return self.add_pending(token)

    def mux_refresh(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.mux_refresh(self.ctx, done_cb)
        return self.add_pending(token)

    def mux_report(self, skip_default: bool, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.mux_report(self.ctx, skip_default, done_cb)
        return self.add_pending(token)


#
#  Wavedrom Utilities
#
def wave_one_probe_to_int(tdata: bytearray, sample_width: int, slice: [int]) -> [int]:
    values = []
    msb, lsb = slice
    bytes_per_sample = (sample_width + 7) // 8
    for sample_low_byte in range(0, len(tdata), bytes_per_sample):
        val = 0
        for bit in range(msb, lsb - 1, -1):
            val = val << 1
            val += 1 if tdata[sample_low_byte + bit // 8] & (1 << (bit % 8)) else 0
        values.append(val)
    return values


def wave_to_int(probe_defs: MILAProbeDefs, wave_dict: Dict) -> Dict:
    """ Break up waveform by probe. Convert to list of int values per probe. """
    tdata = wave_dict[PROP_TRACE_DATA]
    sample_width = wave_dict[PROP_TRACE_WIDTH]
    wave_ints = {
        pname: wave_one_probe_to_int(tdata, sample_width, slice)
        for pname, slice in probe_defs.items()
    }
    return wave_ints


def to_wavedrom_wave_data_color(signal: Dict, start: int, end: int, signal_idx: int) -> None:
    # color 3: yellow, 4: orange, 5: blue, '=': no color
    color = "5" if (signal_idx % 4) == 0 else "="
    vals = signal["int_vals"]
    wave = []
    data = []
    for idx in range(start, end):
        if (idx > start) and (vals[idx] == vals[idx - 1]):
            wave.append(".")
        else:
            wave.append(color)
            data.append(f"{vals[idx]:x}")

    if data:
        signal["data"].append(" ".join(data))
    signal["wave"].append("".join(wave))
    return signal


def to_wavedrom_wave_data(signal: Dict, start: int, end: int) -> None:
    is_one_bit = signal["msb"] == signal["lsb"]
    vals = signal["int_vals"]
    wave = []
    data = []
    for idx in range(start, end):
        if (idx > start) and (vals[idx] == vals[idx - 1]):
            wave.append(".")
        elif is_one_bit:
            wave.append("0" if vals[idx] == 0 else "1")
        else:
            wave.append("=")
            data.append(f"{vals[idx]:x}")

    if data:
        signal["data"].append(" ".join(data))
    signal["wave"].append("".join(wave))
    return signal


def to_wave_json_str(
    signals: [Dict], display_count: int, display_width: int, start_sample: int, do_narrow=True
) -> str:
    def data_str(sig: Dict, index):
        if not sig.get("data", None) or len(sig["data"]) <= index:
            return ""

        return f', data: "{sig["data"][index]}"'

    narrow_str = ", config: {skin:'narrow'}" if do_narrow else ""

    res = ""
    for idx in range(0, display_count):
        head = '<script type="WaveDrom">\n{ signal: [\n'
        tick_start = start_sample + (idx * display_width)
        section_header = f', text: "Samples {tick_start} to {tick_start+display_width-1}"'
        tail = (
            "],\n head: { tick:"
            + str(tick_start)
            + section_header
            + "}"
            + narrow_str
            + " \n"
            + "}\n</script>\n"
        )
        body = [
            " { " + f'name: "{sig["name"]}", wave: "{sig["wave"][idx]}"' + data_str(sig, idx) + "},"
            for sig in signals
        ]
        section_str = head + "\n".join(body) + tail
        res += section_str
    return res


def make_name_with_range(name: str, msb: int, lsb: int) -> str:
    return f"{name}{[msb]}" if msb == lsb else f"{name}[{msb}:{lsb}]"


def wave_to_wave_json_multi(probe_defs: MILAProbeDefs, wave_dict: Dict, display_width: int) -> str:
    wave_ints = wave_to_int(probe_defs, wave_dict)
    signals = [
        {
            "name": make_name_with_range(name, probe_defs[name][0], probe_defs[name][1]),
            "int_vals": ints,
            "wave": [],
            "data": [],
            "msb": probe_defs[name][0],
            "lsb": probe_defs[name][1],
        }
        for name, ints in wave_ints.items()
    ]

    # Break up into sections:
    sample_count = wave_dict["trace_sample_count"]
    start_sample = -wave_dict["trace_trigger_position"]
    display_count = (sample_count + (display_width - 1)) // display_width
    for start in range(0, sample_count, display_width):
        signals_with_wave_data = [
            to_wavedrom_wave_data(signal, start, start + display_width) for signal in signals
        ]
    return to_wave_json_str(signals_with_wave_data, display_count, display_width, start_sample)


def wave_to_wave_json(
    probe_defs: MILAProbeDefs, wave_dict: Dict, center_sample: int = 0, sample_count: int = 64
) -> str:
    wave_ints = wave_to_int(probe_defs, wave_dict)
    signals = [
        {
            "name": make_name_with_range(name, probe_defs[name][0], probe_defs[name][1]),
            "int_vals": ints,
            "wave": [],
            "data": [],
            "msb": probe_defs[name][0],
            "lsb": probe_defs[name][1],
        }
        for name, ints in wave_ints.items()
    ]

    total_sample_count = wave_dict["trace_sample_count"]
    sample_count = min(total_sample_count, sample_count)
    trig_pos_list = wave_dict["trace_trigger_position"]
    trig_pos = trig_pos_list[0]
    start_idx = trig_pos + center_sample - sample_count // 2
    if start_idx < 0:
        start_idx = 0
    elif start_idx + sample_count >= total_sample_count:
        start_idx = total_sample_count - sample_count

    signals_with_wave_data = [
        to_wavedrom_wave_data_color(signal, start_idx, start_idx + sample_count, signal_idx)
        for signal_idx, signal in enumerate(signals)
    ]
    return to_wave_json_str(
        signals_with_wave_data, 1, sample_count, start_idx - trig_pos, do_narrow=sample_count > 50
    )


def display_waveform_in_browser(
    probe_defs: MILAProbeDefs,
    wave_dict: Dict,
    wavedrom_dir: str = ".",
    center_sample: int = 0,
    sample_count: int = 64,
) -> None:
    import webbrowser
    import os

    # create wave json
    wave_data = wave_to_wave_json(probe_defs, wave_dict, center_sample, sample_count)
    filename = "waveform.html"
    f = open(filename, "w")

    message = (
        """
    <html>
      <head>
        <title>Mini-ILA Waveform</title>
      </head>

        <body onload="WaveDrom.ProcessAll()">

        """
        + wave_data
        + f'<script src="{wavedrom_dir}/wavedrom/skins/default.js" type="text/javascript"></script>\n'
        + f'<script src="{wavedrom_dir}/wavedrom/skins/narrow.js" type="text/javascript"></script>\n'
        + f'<script src="{wavedrom_dir}/wavedrom/wavedrom.min.js" type="text/javascript"></script>\n'
        + """

        <hr>
      </body>
    </html>
    """
    )

    f.write(message)
    f.close()

    # Change path to reflect file location
    full_filename = "file:///" + os.getcwd() + "/" + filename
    webbrowser.open_new_tab(full_filename)


def display_waveform_in_jupyter(
    probe_defs: MILAProbeDefs,
    wave_dict: Dict,
    wavedrom_dir: str = ".",
    center_sample: int = 0,
    sample_count: int = 32,
) -> None:
    """ Show wave json waveform in Jupytor notebock cell"""
    import os
    import IPython

    def _is_javascript_present(javascript_path):
        return os.path.isfile(javascript_path)

    # create wave json
    wave_data = wave_to_wave_json(probe_defs, wave_dict, center_sample, sample_count)

    current_path = os.getcwd()
    wavedrom_min_js = os.path.join(current_path, "wavedrom", "wavedrom.min.js")
    wavedrom_skin_js = os.path.join(current_path, "wavedrom", "skins", "default.js")
    wavedrom_skin_narrow_js = os.path.join(current_path, "wavedrom", "skins", "narrow.js")

    if not (
        _is_javascript_present(wavedrom_skin_js)
        and _is_javascript_present(wavedrom_min_js)
        and _is_javascript_present(wavedrom_skin_narrow_js)
    ):
        print("paths", wavedrom_min_js, wavedrom_skin_js, sep="\n")
        raise Exception("wavedrom js not found")

    htmldata = " <h1>Mini-ILA Waveform</h1>" + wave_data
    IPython.core.display.display_html(IPython.core.display.HTML(htmldata))

    jsdata = "WaveDrom.ProcessAll();"
    IPython.core.display.display_javascript(
        IPython.core.display.Javascript(
            data=jsdata,
            # important to have the slashes the unix way.
            lib=[
                "wavedrom/wavedrom.min.js",
                "wavedrom/skins/default.js",
                "wavedrom/skins/narrow.js",
            ],
        )
    )


def find_mila_cores(cs_url: str, hw_url: str = "", silent: bool = False) -> MILACoreClient:

    if hw_url != "":
        server = connect_xicom(cs_url)
        server.connect_remote(hw_url)
        if not silent:
            print(f"Connected to cs_server {cs_url} and hw_server {hw_url}")
    else:
        # single argument passed in is intended to be the actual cs_server
        server = cs_url

    if not silent:
        print(f"CS Server services: {server.services}")

    # Set up core detection and get list of found cores along with context properties
    cs_view = get_cs_view(server)
    if not silent:
        print(f"Searching for DPC in {cs_view}")
    dpc = None
    for node in cs_view.get_children():
        if "DPC" in node.props.get("Name") or "XVC" in node.ctx:
            dpc = cs_view.get_node(node.ctx, CoreParent)
            break

    # Set up all available hardened cores
    dpc.setup_cores()

    if not silent:
        print()
        print(f"DPC: {dpc}")

        print()
        print("ChipScope View:")
        cs_view.print_tree(False)

    # Find MILAs under DPC, returning as generator
    milas = cs_view.find_nodes(dpc, MILACoreClient)

    return milas


def get_mila_by_index(cs_url: str, hw_url: str, idx: int) -> MILACoreClient:

    milas = find_mila_cores(cs_url, hw_url, True)
    mila_list = list(milas)
    mila_count = len(mila_list)

    if (idx < 0) or not (idx < mila_count):
        raise Exception(
            f"Invalid index given to get target MILA: {idx} \
                          \nTotal number of MILA found is: {mila_count}"
        )

    mila = mila_list[idx]

    return mila
