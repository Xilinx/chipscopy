# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

from typing import Dict, List, Union, Tuple
from chipscopy.tcf.services import mila, DoneHWCommand
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy


class MILAProxy(CorePropertyProxy, mila.MILAService):
    def __init__(self, channel):
        super().__init__(channel)
        self._listeners = {}

    #
    #  General methods
    #
    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_command('initialize', (node_id, ), done)

    def terminate(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_command('terminate', (node_id, ), done)

    def write32(self, node_id: str, write_addr: int, data: int, domain_index: int, done: DoneHWCommand) -> None:
        return self.send_command('write32', (node_id, write_addr, data, domain_index), done)

    def read32(self, node_id: str, read_addr: int, read_word_count: int, domain_index: int, done: DoneHWCommand) -> \
            Union[List[int], int]:
        return self.send_command('read32', (node_id, read_addr, read_word_count, domain_index), done)

    #
    # Probe Methods
    #
    def define_probe(self, node_id: str, probe_defs: mila.MILAProbeDefs, done: DoneHWCommand) -> None:
        return self.send_command('defineProbe', (node_id, probe_defs,), done)

    def undefine_probe(self, node_id: str, probe_names: List[str], done: DoneHWCommand) -> None:
        return self.send_command('undefineProbe', (node_id, probe_names,), done)

    def get_probe(self, node_id: str, probe_names: List[str], done: DoneHWCommand) -> mila.MILAProbeDefs:
        return self.send_command('getProbe', (node_id, probe_names,), done)

    def get_probe_match_value(self, node_id: str, probe_names: List[str], done: DoneHWCommand)\
            -> Dict[str, str]:
        return self.send_command('getProbeMatchValue', (node_id, probe_names,), done)

    def set_probe_match_value(self, node_id: str, match_pairs: Dict[str, str], done: DoneHWCommand)\
            -> None:
        return self.send_command('setProbeMatchValue', (node_id, match_pairs,), done)

    #
    # Core Communication Methods
    #
    def arm(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_command('arm', (node_id, ), done)

    def upload(self, node_id: str, done: DoneHWCommand):
        return self.send_command('upload', (node_id,), done)

    #
    #  MUX Methods
    #
    def mux_add_node(self, node_id: str,
                     memory_domain: str,
                     addr: Union[int, None],
                     name: str,
                     long_name: str,
                     has_local_inputs: bool,
                     ch_in0: str,
                     ch_in1: str,
                     done: DoneHWCommand):
        return self.send_command('muxAddNode',
                                 (node_id, memory_domain, addr, name, long_name,
                                  has_local_inputs, ch_in0, ch_in1),
                                 done)

    def mux_build_tree(self, node_id: str,
                       clk_sel_is_1_mux: str,
                       ila_capture_data_sel_muxes: [str],
                       done: DoneHWCommand):
        return self.send_command(
            'muxBuildTree', (node_id, clk_sel_is_1_mux, ila_capture_data_sel_muxes), done)

    def mux_select_inputs(self, node_id: str, mux_node_inputs: [Tuple[str, int]],
                          done: DoneHWCommand) -> None:
        return self.send_command('muxSelectInputs', (node_id, mux_node_inputs), done)

    def mux_get_selected_inputs(self, node_id: str, done: DoneHWCommand):
        return self.send_command('muxGetSelectedInputs', (node_id,), done)

    def mux_commit(self, node_id: str, done: DoneHWCommand):
        return self.send_command('muxCommit', (node_id,), done)

    def mux_refresh(self, node_id: str, done: DoneHWCommand):
        return self.send_command('muxRefresh', (node_id,), done)

    def mux_report(self, node_id: str, skip_default: bool, done: DoneHWCommand):
        return self.send_command('muxReport', (node_id, skip_default), done)
