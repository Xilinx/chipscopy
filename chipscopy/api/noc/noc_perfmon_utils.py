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

import json
import re
from datetime import datetime
from time import sleep
from abc import ABC, abstractmethod

from chipscopy.dm import NodeListener
from chipscopy.dm.harden.noc_perfmon.noc_types import (
    noc_nmu_typedef,
    noc_nsu_typedef,
    ddrmc_noc_typedef,
    noc_node_types,
    ddrmc_main_typedef,
    hbmmc_typedef,
)
from chipscopy.utils.logger import log

# %%
DOMAIN = "noc_perfmon"
epoch = datetime.utcfromtimestamp(0)  # this is stupid, be best python

# %%
# defines
MAX_SAMPLES = 50
ch_map = {"r": 0, "w": 1}


# %%
def get_noc_typedef_from_name(name) -> str:
    nmu_re = re.compile(".*NMU.*", flags=re.IGNORECASE)
    nsu_re = re.compile(".*NSU.*", flags=re.IGNORECASE)
    ddrmc_noc_re = re.compile(".*DDRMC_NOC.*", flags=re.IGNORECASE)
    ddrmc_main_re = re.compile(".*DDRMC_MAIN.*", flags=re.IGNORECASE)
    ddrmc_re = re.compile(".*DDRMC_X.*", flags=re.IGNORECASE)
    hbmmc_re = re.compile(".*HBM_MC_X.*", flags=re.IGNORECASE)

    if nmu_re.match(name):
        return noc_nmu_typedef
    elif nsu_re.match(name):
        return noc_nsu_typedef
    elif ddrmc_noc_re.match(name):
        return ddrmc_noc_typedef
    elif ddrmc_main_re.match(name) or ddrmc_re.match(name):
        return ddrmc_main_typedef
    elif hbmmc_re.match(name):
        return hbmmc_typedef
    else:
        # log[DOMAIN].error(f'unknown type for name: {name}')
        return ""


# %%
class NoCElement(ABC):
    """
    Goal of this class is to serve as storage for the data in nodeUpdate events
    """

    def __init__(
        self,
        name,
        alt_name,
        num_samples,
        sampling_period_ms,
        record_to_file,
        tslide=0,
        counter_freq_mhz=1000.0,
    ):
        self.name = name
        self.alt_name = alt_name
        self.num_samples = num_samples
        self.sampling_period_ms = sampling_period_ms
        self.record_to_file = record_to_file
        self.node_type = get_noc_typedef_from_name(self.name)
        self.tslide = tslide
        self.counter_freq_mhz = counter_freq_mhz

        self.samples = {
            "read_bandwidth": [0] * MAX_SAMPLES,
            "write_bandwidth": [0] * MAX_SAMPLES,
            "avg_read_latency": [0] * MAX_SAMPLES,
            "avg_write_latency": [0] * MAX_SAMPLES,
            "flags": [],
            "ts": [],
            "type": self.node_type,
        }
        self.raw_trace_data = {}

    @abstractmethod
    def update_node(self, tcf_node, updated_keys):  # pragma: no cover
        pass

    def get_axis_metrics(self, axis, view, pc):
        # pc is only for HBM
        for metric in self.axis_metrics[axis][view]:
            yield metric

    def record_bw_lat(
        self,
        read_bytes,
        write_bytes,
        read_bytes_per_s,
        write_bytes_per_s,
        avg_read_latency,
        avg_write_latency,
    ):
        self.samples["read_bandwidth"].append(read_bytes_per_s)
        self.samples["write_bandwidth"].append(write_bytes_per_s)
        self.samples["avg_read_latency"].append(avg_read_latency)
        self.samples["avg_write_latency"].append(avg_write_latency)
        log[DOMAIN].info(
            f"{self.name}: rb: {read_bytes}, wb: {write_bytes}, "
            + f"rbw: {read_bytes_per_s}, wbw: {write_bytes_per_s}, "
            + f"arl: {avg_read_latency}, awl: {avg_write_latency}"
        )

    def trim_and_log(self, raw_trace_data):
        # trim samples down:
        for _, sample_data in self.samples.items():
            if len(sample_data) > MAX_SAMPLES:
                sample_data.pop(0)

        if self.record_to_file:
            date_handler = lambda obj: (
                obj.isoformat()
                if isinstance(obj, (datetime, datetime.date))
                else json.JSONEncoder().default(obj)
            )
            with open("raw_trace_data.json", "a") as ofh:
                json.dump(raw_trace_data, ofh, default=date_handler)
                ofh.write("\n")
            with open("scaled_trace_data.json", "a") as ofh:
                data_to_dump = {self.name: self.samples}
                json.dump(data_to_dump, ofh, default=date_handler)
                ofh.write("\n")

        self.raw_trace_data = raw_trace_data


# %%
class DDRMC(NoCElement):
    dc_metrics_map = {
        0: "activates",
        1: "read_cas",
        2: "write_cas",
        3: "precharge",
        4: "precharge_all",
        5: "refresh",
        6: "idle",
        7: "overhead",
        8: "bus_turnarounds",
    }

    def __init__(self, *args):
        """
        for DDRMC 'ddrmc_main_X' shall be the name and 'ddrmc_noc_X' shall serve as the alternate name
        :param name:
        :param alt_name:
        """
        super().__init__(*args)
        # add DC aggregate, NSU agg, and NSU port metrics
        for ch in range(0, 2):
            for metric in DDRMC.dc_metrics_map.values():
                self.samples.update({f"dc{ch}_{metric}": [0] * MAX_SAMPLES})
                if ch == 0:
                    self.samples.update({f"agg_{metric}": [0] * MAX_SAMPLES})
            self.samples.update({f"dc{ch}_flags": [0] * MAX_SAMPLES})

        for nsu in range(0, 4):
            self.samples.update({f"nsu{nsu}_write_bandwidth": [0] * MAX_SAMPLES})
            self.samples.update({f"nsu{nsu}_read_bandwidth": [0] * MAX_SAMPLES})
            self.samples.update({f"nsu{nsu}_write_latency": [0] * MAX_SAMPLES})
            self.samples.update({f"nsu{nsu}_read_latency": [0] * MAX_SAMPLES})

        self.axis_metrics = {
            "left_axis": {
                "bandwidth": ["write_bandwidth", "read_bandwidth"],
                "latency": ["avg_write_latency", "avg_read_latency"],
                "mem": [
                    "agg_activates",
                    "agg_read_cas",
                    "agg_write_cas",
                    "agg_precharge",
                    "agg_precharge_all",
                    "agg_refresh",
                    "agg_idle",
                    "agg_overhead",
                    "agg_bus_turnarounds",
                ],
            },
            "right_axis": {"bandwidth": [], "latency": [], "mem": []},
        }

    def update_node(self, tcf_node, updated_keys):
        self.num_samples -= 1
        raw_trace_data = {
            "type": self.node_type,
            "name": self.name,
            # 'ts': (datetime.now() - self.start_time) + epoch,
            "ts": datetime.now(),
            "r": {},
            "w": {},
        }

        tcf_node_type = get_noc_typedef_from_name(tcf_node.Name)

        if tcf_node_type == ddrmc_noc_typedef:
            for ch, mon in ch_map.items():
                raw_trace_data[ch]["lacc"] = []
                raw_trace_data[ch]["burst_count"] = []
                raw_trace_data[ch]["byte_count"] = []
                raw_trace_data[ch]["flags"] = []
                for nsu in range(0, 4):
                    lacc = tcf_node[f"nsu{nsu}_perf_mon_{mon}_0"]
                    raw_trace_data[ch]["lacc"].append(lacc & 0x7FFFFFFF)
                    raw_trace_data[ch]["burst_count"].append(tcf_node[f"nsu{nsu}_perf_mon_{mon}_1"])
                    raw_trace_data[ch]["byte_count"].append(tcf_node[f"nsu{nsu}_perf_mon_{mon}_2"])
                    raw_trace_data[ch]["flags"].append((lacc & 0x80000000) >> 31)

            # bandwidth
            rf = 0
            wf = 0
            for nsu in range(0, 4):
                rf += raw_trace_data["r"]["burst_count"][nsu]
                wf += raw_trace_data["w"]["burst_count"][nsu]
            read_bytes = rf * 128 / 8
            write_bytes = wf * 128 / 8
            read_bytes_per_s = read_bytes / (self.sampling_period_ms / 1000)
            write_bytes_per_s = write_bytes / (self.sampling_period_ms / 1000)

            # flags
            flags = []
            for ch in ["r", "w"]:
                flag = 0
                for nsu in range(0, 4):
                    flag += raw_trace_data[ch]["flags"][nsu]
                if flag != 0:
                    flags.append(f"{ch}_overflow")
            self.samples["flags"].append(flags)

            # latency
            avg_lat = {"r": 0, "w": 0}
            for ch in ["r", "w"]:
                agg_lat = 0
                agg_burst = 0
                for nsu in range(0, 4):
                    agg_lat += raw_trace_data[ch]["lacc"][nsu]
                    agg_burst += raw_trace_data[ch]["burst_count"][nsu]
                if agg_burst == 0:
                    agg_burst = 1
                avg_lat[ch] = float(agg_lat) / float(agg_burst)

            # common op
            self.record_bw_lat(
                read_bytes,
                write_bytes,
                read_bytes_per_s,
                write_bytes_per_s,
                avg_lat["r"],
                avg_lat["w"],
            )

        if tcf_node_type == ddrmc_main_typedef:
            for ch in range(0, 2):
                flags = 0
                for m_index, metric in DDRMC.dc_metrics_map.items():
                    agg_metric = f"agg_{metric}"
                    disagg_metric = f"dc{ch}_{metric}"
                    self.samples[disagg_metric].append(0)
                    if ch == 0:
                        self.samples[agg_metric].append(0)
                    data = tcf_node[f"dc{ch}_perf_mon_{m_index}"]
                    raw_trace_data[disagg_metric] = data
                    overflow = data & 0x80000000 == 0x80000000
                    data &= 0x7FFF_FFFF
                    if overflow:
                        flags |= 1 << m_index  # overflow
                    self.samples[disagg_metric][-1] = data
                    self.samples[agg_metric][-1] += data
                    # need to trim here or we can get a dim mismatch when plotting happens
                    # unique issue for ddmrc, since it's two nodes with polls coming in at different rates
                    if len(self.samples[disagg_metric]) > MAX_SAMPLES:
                        self.samples[disagg_metric].pop(0)
                    if ch == 1:
                        if len(self.samples[agg_metric]) > MAX_SAMPLES:
                            self.samples[agg_metric].pop(0)
                self.samples[f"dc{ch}_flags"].append(flags)

        # timestamp handling
        # the way the polls are created the NA reports AFTER the main, so when this event is received, update plots
        if tcf_node_type == ddrmc_noc_typedef:
            time_delta = raw_trace_data["ts"].strftime("%M:%S.") + str(
                int(raw_trace_data["ts"].microsecond / 1000)
            )
            self.samples["ts"].append(time_delta)
            self.trim_and_log(raw_trace_data)


class NoCMasterSlave(NoCElement):
    def __init__(self, *args):
        super().__init__(*args)
        self.samples.update(
            {
                "min_r_latency": [0] * MAX_SAMPLES,
                "max_r_latency": [0] * MAX_SAMPLES,
                "min_w_latency": [0] * MAX_SAMPLES,
                "max_w_latency": [0] * MAX_SAMPLES,
            }
        )
        self.axis_metrics = {
            "left_axis": {
                "bandwidth": ["write_bandwidth", "read_bandwidth"],
                "latency": [
                    "avg_write_latency",
                    "avg_read_latency",
                    "min_w_latency",
                    "max_w_latency",
                    "min_r_latency",
                    "max_r_latency",
                ],
                "mem": [],
            },
            "right_axis": {"bandwidth": [], "latency": [], "mem": []},
        }

    def update_node(self, tcf_node, updated_keys):
        raw_trace_data = {
            "type": self.node_type,
            "name": self.name,
            # 'ts': (datetime.now() - self.start_time) + epoch,
            "ts": datetime.now(),
            "r": {},
            "w": {},
        }
        for ch, mon in ch_map.items():
            raw_trace_data[ch]["burst_count"] = tcf_node[f"reg_perf_mon{mon}_burst_cnt"]
            raw_trace_data[ch]["byte_count"] = tcf_node[f"reg_perf_mon{mon}_byte_cnt_lwr"] + (
                (tcf_node[f"reg_perf_mon{mon}_cnt_and_ofl"] & 0xFF) << 32
            )
            raw_trace_data[ch]["flags"] = (tcf_node[f"reg_perf_mon{mon}_cnt_and_ofl"] & 0x1F00) >> 8
            raw_trace_data[ch]["lacc"] = (
                tcf_node[f"reg_perf_mon{mon}_latency_acc_lwr"]
                + ((tcf_node[f"reg_perf_mon{mon}_latency_acc_upr"] & 0xFF) << 32)
            ) << self.tslide
            raw_trace_data[ch]["lmax"] = tcf_node[f"reg_perf_mon{mon}_latency_max"] << self.tslide
            raw_trace_data[ch]["lmin"] = tcf_node[f"reg_perf_mon{mon}_latency_min"] << self.tslide

        # bandwidth
        read_bytes = raw_trace_data["r"]["byte_count"]
        write_bytes = raw_trace_data["w"]["byte_count"]
        read_bytes_per_s = read_bytes * 1000 / self.sampling_period_ms
        write_bytes_per_s = write_bytes * 1000 / self.sampling_period_ms
        # latency and flags
        flags = []
        for ch in ["r", "w"]:
            self.samples[f"min_{ch}_latency"].append(raw_trace_data[ch]["lmin"])
            self.samples[f"max_{ch}_latency"].append(raw_trace_data[ch]["lmax"])
            # flags
            raw_flags = raw_trace_data[ch]["flags"]
            if raw_flags != 0:
                if (raw_flags & 0x10) == 0x10:
                    flags.append(f"{ch}_byte_count_overflow")
                if (raw_flags & 0x08) == 0x08:
                    flags.append(f"{ch}_burst_count_overflow")
                if (raw_flags & 0x04) == 0x04:
                    flags.append(f"{ch}_accumulated_latency_overflow")
                if (raw_flags & 0x02) == 0x02:
                    flags.append(f"{ch}_max_latency_overflow")
                if (raw_flags & 0x01) == 0x01:
                    flags.append(f"{ch}_min_latency_overflow")
        self.samples["flags"].append(flags)

        # latency
        avg_lat = {"r": 0, "w": 0}
        for ch in ["r", "w"]:
            avg_lat[ch] = raw_trace_data[ch]["lacc"] / (
                raw_trace_data[ch]["burst_count"] if raw_trace_data[ch]["burst_count"] != 0 else 1
            )
        self.record_bw_lat(
            read_bytes, write_bytes, read_bytes_per_s, write_bytes_per_s, avg_lat["r"], avg_lat["w"]
        )
        time_delta = raw_trace_data["ts"].strftime("%M:%S.") + str(
            int(raw_trace_data["ts"].microsecond / 1000)
        )
        self.samples["ts"].append(time_delta)
        self.trim_and_log(raw_trace_data)


class NoCPerfMonNodeListener(NodeListener):
    """
    Example Listener class that will print out metrics from NoC nodes (NMU|NSU|DDRMC)

    """

    def __init__(
        self,
        sampling_period_ms,
        num_samples,
        enabled_nodes,
        record_to_file,
        npi_clk_freq=299997009,
        noc_clk_freq=999989990,
        extended_monitor_config=None,
    ):
        self.sampling_period_ms = sampling_period_ms
        self.num_samples = {}
        self.npi_clk_freq = npi_clk_freq
        self.noc_clk_freq = noc_clk_freq
        self.plotter = None
        super().__init__()
        # setup logging
        log.enable_domain([DOMAIN])
        log.change_log_level("WARNING")
        # self.start_time = datetime.now()
        self.noc_elements = {}  # storage for the active monitors
        self.unique_elements = (
            {}
        )  # same objects from above, but with alt mapping removed -- for plot utils

        # build data structure for holding historical data
        for elem in enabled_nodes:
            tslide = 0
            if extended_monitor_config is not None:
                if elem in extended_monitor_config.keys():
                    node_config = extended_monitor_config[elem]
                    if "tslide" in node_config:
                        tslide = node_config["tslide"]
            node_type = get_noc_typedef_from_name(elem)
            if node_type in [noc_nmu_typedef, noc_nsu_typedef]:
                storage_node = NoCMasterSlave(
                    elem.lower(),
                    None,
                    num_samples,
                    sampling_period_ms["NPI"],
                    record_to_file,
                    tslide,
                    npi_clk_freq / 1000000.0,
                )
                self.noc_elements[elem.lower()] = storage_node
                self.unique_elements[elem.lower()] = storage_node
            elif node_type in [ddrmc_main_typedef]:
                alt_name = "ddrmc_noc_" + elem.split("_")[-1]
                node = DDRMC(
                    elem.lower(),
                    alt_name.lower(),
                    num_samples,
                    sampling_period_ms["NoC"],
                    record_to_file,
                    tslide,
                    noc_clk_freq / 1000000.0,
                )
                self.noc_elements[elem.lower()] = node
                self.noc_elements[alt_name.lower()] = node
                self.unique_elements[elem.lower()] = node
            elif node_type in [hbmmc_typedef]:
                from chipscopy.api.noc.graphing.hbmmc import HBMMC

                node = HBMMC(
                    elem.lower(),
                    elem.lower(),
                    num_samples,
                    sampling_period_ms[elem],
                    record_to_file,
                    tslide,
                    npi_clk_freq / 1000000.0,
                )
                self.noc_elements[elem.lower()] = node
                self.unique_elements[elem.lower()] = node
            else:  # pragma: no cover
                raise Exception(f"Error, unsupported node: {elem}, type: {node_type}")

    def node_changed(self, node, updated_keys):
        node_type = get_noc_typedef_from_name(node.Name)
        name = node.Name.lower()
        if node_type in noc_node_types and node.Name.lower() in self.noc_elements.keys():
            log[DOMAIN].debug(f"{node.type}: {node.Name}")

            # dispatch the class handler
            self.noc_elements[name].update_node(node, updated_keys)

            # finally update plots
            if self.plotter is not None and node_type is not ddrmc_main_typedef:
                self.plotter.update(self.noc_elements[name])

    def link_plotter(self, plotter):
        self.plotter = plotter
        self.plotter.listener = self


class PerfTGController:
    def __init__(self, base_address, device, vio=None):
        self.base_address = base_address
        self.device = device
        self.vio = vio
        self.instr_ba = self.base_address + 0x8000
        self.ctrl = self.base_address + 0x4000
        self.tg_start = self.base_address + 0x4004
        self.instr_0 = []
        self.instr_1 = []
        self.supported_patterns = {
            "Write Linear": [
                [
                    0xFF200000,
                    0x00080000,
                    0x00000002,
                    0x00000000,
                    0xFFE00000,
                    0x000FFFFF,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00010020,
                    0x00143500,
                    0x0000048C,
                    0x0,
                ],
                [
                    0x00000001,
                    0x00100000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00020000,
                    0x00000000,
                    0x00000000,
                    0x0,
                ],
            ],
            "Read Linear": [
                [
                    0xFF200000,
                    0x00000000,
                    0x00000002,
                    0x00000000,
                    0xFFE00000,
                    0x000FFFFF,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00010020,
                    0x00143500,
                    0x0000048E,
                    0x0,
                ],
                [
                    0x00000001,
                    0x00100000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00000000,
                    0x00020000,
                    0x00000000,
                    0x00000000,
                    0x0,
                ],
            ],
        }
        self.active_pattern = "Write Linear"
        self.trigger_block_rst_probe = None
        self.tg_rst_probe = None
        for probe in self.vio.probe_names:
            if probe.split("/")[-1] == "noc_sim_trig_rst_n":
                self.trigger_block_rst_probe = probe
            if probe.split("/")[-1] == "noc_tg_tg_rst_n":
                self.tg_rst_probe = probe

    def start(self):
        self.device.memory_write(self.tg_start, [0x1])
        # CR-1062874
        # Second write of the ctrl reg is required for the start command to be effective.
        sleep(0.5)
        self.device.memory_write(self.tg_start, [0x1])

    def stop(self):
        # this doesn't seem to be doing much
        self.device.memory_write(self.tg_start, [0x0])

        self._soft_reset()
        self._clear_instruction_memory()

    def block_reset(self):

        if self.vio is not None:
            self.vio.write_probes(
                {
                    self.trigger_block_rst_probe: 0x0,
                    self.tg_rst_probe: 0x0,
                }
            )
            self.vio.write_probes(
                {
                    self.trigger_block_rst_probe: 0x1,
                    self.tg_rst_probe: 0x1,
                }
            )

    def program(self):
        self._soft_reset()
        self.device.memory_write(self.instr_ba, self.supported_patterns[self.active_pattern][0])
        self.device.memory_write(
            self.instr_ba + 0x40, self.supported_patterns[self.active_pattern][1]
        )

    def set_active_pattern(self, pattern):
        if pattern not in self.supported_patterns.keys():
            raise ValueError(f"Unsupported pattern: {pattern}")
        else:
            self.active_pattern = pattern

    def _clear_instruction_memory(self):
        self.device.memory_write(self.instr_ba, [0x0] * 13)
        self.device.memory_write(self.instr_ba + 0x40, [0x0] * 13)

    def _soft_reset(self):
        self.device.memory_write(self.ctrl, [0x0])
        self.device.memory_write(self.ctrl, [0x1])
