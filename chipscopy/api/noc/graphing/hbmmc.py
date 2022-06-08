# Copyright 2022 Xilinx, Inc.
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
from datetime import datetime

from chipscopy.api.noc.noc_perfmon_utils import NoCElement, get_noc_typedef_from_name, MAX_SAMPLES

pc_map = {"PC0": 0, "PC1": 1}

TG_EFF_SCALE = 1.042611


class HBMMC(NoCElement):
    pm_regs = [
        "hbmmc_mc_pm_read_pc0",
        "hbmmc_mc_pm_write_pc0",
        "hbmmc_mc_pm_read_ap_pc0",
        "hbmmc_mc_pm_write_ap_pc0",
        "hbmmc_mc_pm_sch_overhead_pc0",
        "hbmmc_mc_pm_sch_ooo_pc0",
        "hbmmc_mc_pm_sch_snub_pc0",
        "hbmmc_mc_pm_sch_rwswitch_pc0",
        "hbmmc_mc_pm_scrub_pc0",
        "hbmmc_mc_pm_rmw_pc0",
        "hbmmc_mc_pm_activate_pc0",
        "hbmmc_mc_pm_pchg_pc0",
        "hbmmc_mc_pm_preall_pc0",
        "hbmmc_mc_pm_sbrf_pc0",
        "hbmmc_mc_pm_grefresh_pc0",
        "hbmmc_mc_pm_read_pc1",
        "hbmmc_mc_pm_write_pc1",
        "hbmmc_mc_pm_read_ap_pc1",
        "hbmmc_mc_pm_write_ap_pc1",
        "hbmmc_mc_pm_sch_overhead_pc1",
        "hbmmc_mc_pm_sch_ooo_pc1",
        "hbmmc_mc_pm_sch_snub_pc1",
        "hbmmc_mc_pm_sch_rwswitch_pc1",
        "hbmmc_mc_pm_scrub_pc1",
        "hbmmc_mc_pm_rmw_pc1",
        "hbmmc_mc_pm_activate_pc1",
        "hbmmc_mc_pm_pchg_pc1",
        "hbmmc_mc_pm_preall_pc1",
        "hbmmc_mc_pm_sbrf_pc1",
        "hbmmc_mc_pm_grefresh_pc1",
        # TODO ??
        # 'hbmmc_mc_pm_pde_cnt',
        # 'hbmmc_mc_pm_sre_cnt',
        # 'hbmmc_mc_pm_pdx_cnt',
        # 'hbmmc_mc_pm_srx_cnt',
        # 'hbmmc_mc_pm_mrs_cnt',
        # 'hbmmc_mc_pm_interval_time'
    ]
    na_count = 2  # number of NoC Agent sub-blocks per HBMMC instance
    pc_count = 2  # number of psuedo channels per HBMMC instance
    pc_regexes = {
        "PC0": re.compile(".*pc0.*", re.IGNORECASE),
        "PC1": re.compile(".*pc1.*", re.IGNORECASE),
    }

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
        """
        for HBM_MC 'HBM_MC_x' shall be the name and 'HBM_MC_NA_x' shall serve as the alternate name
        :param name:
        :param alt_name:
        """
        self.name = name
        self.alt_name = alt_name
        self.num_samples = num_samples
        self.sampling_period_ms = sampling_period_ms
        self.record_to_file = record_to_file
        self.node_type = get_noc_typedef_from_name(self.name)
        self.tslide = tslide
        self.counter_freq_mhz = counter_freq_mhz

        self.samples = {
            "read_bandwidth_pc0": [0] * MAX_SAMPLES,
            "read_bandwidth_pc1": [0] * MAX_SAMPLES,
            "write_bandwidth_pc0": [0] * MAX_SAMPLES,
            "write_bandwidth_pc1": [0] * MAX_SAMPLES,
            "total_bandwidth_pc0": [0] * MAX_SAMPLES,
            "total_bandwidth_pc1": [0] * MAX_SAMPLES,
            "ts": [],
            "type": self.node_type,
        }
        self.raw_trace_data = {}

        for metric in HBMMC.pm_regs:
            self.samples.update({f"{metric}": [0] * MAX_SAMPLES})

        self.axis_metrics = {
            "left_axis": {
                "bandwidth": [
                    "write_bandwidth_pc0",
                    "write_bandwidth_pc1",
                    "read_bandwidth_pc0",
                    "read_bandwidth_pc1",
                    "total_bandwidth_pc0",
                    "total_bandwidth_pc1",
                ],
                "latency": [],
                "mem": HBMMC.pm_regs,
            },
            "right_axis": {"bandwidth": [], "latency": [], "mem": []},
        }

    def get_axis_metrics(self, axis, view, pc):
        for metric in self.axis_metrics[axis][view]:
            if HBMMC.pc_regexes[pc].match(metric):
                yield metric

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

        for reg in HBMMC.pm_regs:
            self.samples[f"{reg}"].append(tcf_node.props[f"{reg}"])

        # bandwidth
        rf = read_bytes_per_s = [0] * HBMMC.pc_count
        wf = write_bytes_per_s = [0] * HBMMC.pc_count

        for na_idx in range(0, HBMMC.na_count):
            for pc_idx in range(0, HBMMC.pc_count):
                rf[pc_idx] += tcf_node.props[
                    f"na{na_idx}.hbmmc_na{na_idx}_na_pm_read_data_p{pc_idx}"
                ]
                wf[pc_idx] += tcf_node.props[
                    f"na{na_idx}.hbmmc_na{na_idx}_na_pm_write_data_p{pc_idx}"
                ]
        for pc_idx in range(0, HBMMC.pc_count):
            # TODO remove wompus constant
            rf[pc_idx] = rf[pc_idx] * 128 / 8
            read_bytes_per_s[pc_idx] = rf[pc_idx] / (self.sampling_period_ms / 1000)
            self.samples[f"read_bandwidth_pc{pc_idx}"].append(read_bytes_per_s[pc_idx])
            # TODO remove wompus constant
            wf[pc_idx] = wf[pc_idx] * 128 / 8
            write_bytes_per_s[pc_idx] = wf[pc_idx] / (self.sampling_period_ms / 1000)
            self.samples[f"write_bandwidth_pc{pc_idx}"].append(write_bytes_per_s[pc_idx])
            self.samples[f"total_bandwidth_pc{pc_idx}"].append(
                read_bytes_per_s[pc_idx] + write_bytes_per_s[pc_idx]
            )

        # timestamp handling
        time_delta = raw_trace_data["ts"].strftime("%M:%S.") + str(
            int(raw_trace_data["ts"].microsecond / 1000)
        )
        self.samples["ts"].append(time_delta)
        self.trim_and_log(raw_trace_data)
