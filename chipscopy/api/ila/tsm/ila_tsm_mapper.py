# Copyright (C) 2022, Xilinx, Inc.
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
import copy
from typing import List, Dict, Callable

from chipscopy.api.ila.tsm.ila_tsm_data import (
    ILATsmData,
    ILATsmAction,
    MAX_STATE_COUNT,
    ILATsmState,
    ILATsmCondition,
    COUNTER_COUNT,
    ILATsmErrorListener,
    ILATsmMatchUnit,
    TABLE_ROWS_PER_STATE,
    MAX_CONDITION_COUNT_PER_STATE,
)
from chipscopy.shared.ila_mapper import IlaMapper, MapPortSeq, port_map_str_to_port_seqs, to_json


def select_counter_actions(tsm_data: ILATsmData) -> None:
    """
    Update branch actions, with counter selections, based their "next_state".
    """

    # Set state counter_index, by looking at branch conditions.
    for state in tsm_data.states:
        # Default value, when counter is not used in state conditions.
        counter_index = 0
        for branch in state.branches:
            if branch.condition and branch.condition.counter_compare:
                counter_index = branch.condition.counter_compare.counter_index
                break
        state.counter_index = counter_index

    # Update branch actions, with next counter to use.
    for state in tsm_data.states:
        for branch in state.branches:
            counter_index = tsm_data.states[branch.next_state].counter_index
            branch.actions = ILATsmAction.add_select_counter_action(branch.actions, counter_index)


def create_tsm_table_actions(tsm_data: ILATsmData) -> List[ILATsmAction]:
    """
    TSM table has 8 rows (or words) per state. There are maximum 16 states.
    TSM Address inputs, see class ILATsmInput.
    Args:
        tsm_data (ILATsmData): Parsed information.

    Returns: List of actions. One action object per "row" or address.

    """
    tsm_actions = []
    for state in tsm_data.states:
        # States have the 4 most significant bits in the TSM address.
        for if_mux in [False, True]:
            # "if mux" is the next bit in the TSM address
            for else_if_mux in [False, True]:
                # "else if mux" is the next bit in the TSM address
                for counter_mux in [False, True]:
                    # "counter mux" is the next bit in the TSM address, and the lsb.
                    action = get_actions_tsm_for_inputs(state, if_mux, else_if_mux, counter_mux)
                    tsm_actions.append(action)

    # Add un-used states
    unused_table_rows = (MAX_STATE_COUNT - len(tsm_data.states)) * TABLE_ROWS_PER_STATE
    un_used_state_actions = [ILATsmAction.DEFAULT] * unused_table_rows
    tsm_actions.extend(un_used_state_actions)
    return tsm_actions


def get_actions_tsm_for_inputs(
    state: ILATsmState, if_mux: bool, else_if_mux: bool, counter_mux
) -> ILATsmAction:
    """
    1 branch: No if-branch, no if-else branch exists.
    2 branches: An if-branch and an else-branch exist. No else-if branch.
    3 branches: All 3 branches exist: if, else-if, else:
    """
    branch = None
    if len(state.branches) > 1:
        # Try state if condition.
        if eval_condition(state.branches[0].condition, if_mux, counter_mux):
            branch = state.branches[0]

    if not branch and len(state.branches) > 2:
        # Try state "else-if" condition.
        if eval_condition(state.branches[1].condition, else_if_mux, counter_mux):
            branch = state.branches[1]

    if not branch:
        # Use last branch.
        branch = state.branches[-1]

    return branch.actions


def eval_condition(cond: ILATsmCondition, probe_mux: bool, in_counter_mux: bool) -> bool:
    """
    Evaluate a branch condition.

    Args:
        cond (ILATsmCondition): A branch condition.
        probe_mux (bool): True if the probe expression within the condition, is True.
        in_counter_mux (bool): True if the counter expression is True.

    Returns: True if the whole condition is True.

    """
    counter_mux = not in_counter_mux if cond.is_invert_counter_mux() else in_counter_mux
    if len(cond.match_units) == 0:
        # No probes in condition, just counter.
        res = counter_mux
    elif cond.counter_operator is None:
        # No counter, just probes in the condition.
        res = probe_mux
    elif cond.counter_operator == "||":
        # probe condition or'ed with counter.
        res = probe_mux or counter_mux
    else:
        # probe condition and'ed with counter.
        res = probe_mux and counter_mux
    return res


def map_tsm_actions_to_props(actions: [ILATsmAction]) -> Dict[str, str]:
    """

    Args:
        actions ([ILATsmAction): list of tsm actions

    Returns: TSM register value is binary string, with new-line char between tsm words.
    """
    bin_values = [f"{action.value:024b}" for action in actions]
    return {"fsm": "\n".join(bin_values)}


def map_tsm_counters_to_props(tsm_data: ILATsmData) -> Dict[str, str]:
    counter_values = {}
    for state in tsm_data.states:
        for branch in state.branches:
            if branch.condition and branch.condition.counter_compare:
                ccmp = branch.condition.counter_compare
                # Convert binary string to unsigned int string.
                counter_values[ccmp.counter_index] = str(int(ccmp.compare_value, 2))

    # Value is an integer, as a string.
    res = {f"counter{idx}_config": counter_values.get(idx, "0") for idx in range(COUNTER_COUNT)}
    return res


def map_tsm_mu_tc_to_props(
    tsm_data: ILATsmData, has_basic_capture_control: bool, error_listener: ILATsmErrorListener
) -> Dict[str, str]:
    """

    Args:
        tsm_data:
        has_basic_capture_control: True reserves first port match unit for basic capture control.
        error_listener:

    Returns: tcf ila property settings.

    """

    def create_mu_index_function(skip_first_mu: bool) -> Callable[[int, int], int]:
        """

        Args:
            skip_first_mu: True, means do not use the first match unit for each port.

        Returns: Function get_mu_index(port_index, mu_index_within_port) : ila_match_unit_index

        """
        # Create dictionary  (port_index, mu_index_within_port): mu_index
        mu_index_by_port_index_and_mu_index_with_port = {
            (pp.index, pmu_index): mu_index
            for pp in tsm_data.ports
            for pmu_index, mu_index in enumerate(pp.match_units)
        }

        def get_mu_index_fn(port_index: int, mu_index_within_port: int) -> int:
            if skip_first_mu:
                mu_index_within_port += 1
            mu_index = mu_index_by_port_index_and_mu_index_with_port.get(
                (port_index, mu_index_within_port), -1
            )
            if mu_index < 0:
                error_listener.report_error(
                    None, None, "Internal error mapping Trigger State Machine to Match Units."
                )
            return mu_index

        return get_mu_index_fn

    def add_probe_value_to_ports(
        ila_mapper: IlaMapper, tc_index: int, tsm_mu: ILATsmMatchUnit, seqs: [MapPortSeq]
    ) -> None:
        value = tsm_mu.compare_value
        idx = len(value)
        vals = []
        for seq in seqs:
            vals.append(value[idx - (seq.high_idx - seq.low_idx + 1) : idx])
            idx -= seq.high_idx - seq.low_idx + 1
        for seq, val in zip(seqs, vals):
            ila_mapper.add_probe_value(
                tc_index,
                tsm_mu.probe.name,
                seq.port_idx,
                seq.low_idx,
                tsm_mu.get_compare_operator(),
                val,
            )

    #
    mapper_ports = [(pp.bit_width, len(pp.match_units)) for pp in tsm_data.ports]
    if has_basic_capture_control:
        # First MU per port is reserved for capture control.
        mapper_ports = [
            (width, mu_count if mu_count <= 0 else mu_count - 1) for width, mu_count in mapper_ports
        ]
    mapper: IlaMapper = IlaMapper(is_basic_capture=False)
    mapper.add_ports(mapper_ports)

    for state in tsm_data.states:
        for branch_index, branch in enumerate(state.branches):
            if not branch.condition or not branch.condition.match_units:
                # No condition with probe match values, for this branch.
                continue

            condition_index = mapper.add_condition(
                branch.condition.get_mapper_probe_operator(),
                make_tc_name(state.index, branch_index),
            )
            for tsm_mu in branch.condition.match_units:
                seqs = port_map_str_to_port_seqs(tsm_mu.probe.name, tsm_mu.probe.map)
                add_probe_value_to_ports(mapper, condition_index, tsm_mu, seqs)

    # Map to match units, get result or overflow messages.
    status, overflow_message = mapper.map(skip_overflow_messages=False)
    if not status:
        error_listener.report_error(
            None, None, f"Unable to fit probe values on port match units:\n {overflow_message}"
        )
        # print(to_json(mapper))
        return {}
    else:
        # print(to_json(mapper))
        return mapper.get_reg_mu_mapping(
            tsm_data.get_match_unit_count(), create_mu_index_function(has_basic_capture_control)
        )


def make_tc_name(state_index: int, branch_index: int) -> str:
    index = state_index + branch_index * MAX_STATE_COUNT
    return f"tc{index}"


def init_fsm_tc_props(tsm_data: ILATsmData) -> Dict[str, str]:
    # Make init values for all Trigger conditions in FSM.
    unused_value = IlaMapper.get_unused_tc_value(tsm_data.get_match_unit_count())
    init_props = {
        make_tc_name(st, br): unused_value
        for st in range(MAX_STATE_COUNT)
        for br in range(MAX_CONDITION_COUNT_PER_STATE)
    }
    return init_props


def map_tsm_to_props(
    tsm_data: ILATsmData, has_basic_capture_control: bool, error_listener: ILATsmErrorListener
) -> Dict[str, str]:
    props = init_fsm_tc_props(tsm_data)
    mu_tc_props = map_tsm_mu_tc_to_props(tsm_data, has_basic_capture_control, error_listener)
    props.update(mu_tc_props)
    props.update(map_tsm_counters_to_props(tsm_data))
    tsm_row_actions = create_tsm_table_actions(tsm_data)
    props.update(map_tsm_actions_to_props(tsm_row_actions))
    return props


def dump_fsm_regs(regs: Dict[str, str], base: int = 2) -> Dict[str, str]:
    actions = [ILATsmAction(int(num, base)) for num in regs["fsm"].splitlines()]
    res = []
    it = iter(actions)
    for st in range(MAX_STATE_COUNT):
        res.append(f"\nInputs:if-elif-counter - State {st} Actions")
        for row in range(TABLE_ROWS_PER_STATE):
            if row == 4:
                res.append("")
            res.append(f"{row:03b}  " + next(it).dump())
    return {"fsm": "\n".join(res)}


def dump_tsm_regs(regs: Dict[str, str]) -> Dict[str, str]:
    # Just the fsm reg value is re-formatted.
    dump_regs = copy.copy(regs)
    dump_regs.update(dump_fsm_regs(dump_regs))
    return dump_regs
