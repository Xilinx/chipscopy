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
import enum
from collections import UserList, defaultdict
from typing import Dict, List, Union, Iterable, Any, Optional, Set, NamedTuple

from antlr4 import ParserRuleContext
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Tree import TerminalNodeImpl

from chipscopy.api.ila.tsm.ILATsmParser import ILATsmParser
from chipscopy.api.ila.tsm.ILATsmVisitor import ILATsmVisitor
from chipscopy.api.ila.tsm.ila_tsm_data import (
    ILATsmData,
    ILATsmErrorListener,
    ILATsmMatchUnit,
    ILATsmCounterCompare,
    ILATsmAction,
    ILATsmActionPair,
    ILATsmBranch,
    ILATsmState,
    ILATsmCondition,
)
from chipscopy.api.ila import ILAProbe, ILA_MATCH_BIT_VALUES, ILA_MATCH_OPERATORS
from chipscopy.api.ila.tsm.ila_tsm_mapper import select_counter_actions
from chipscopy.shared.ila_util import hex_to_bin_str


class CounterMatch(NamedTuple):
    ctx: ILATsmParser.Counter_matchContext
    cmp: ILATsmCounterCompare


class ILATsmCheckAndBuild(ILATsmVisitor):
    # Semantic checks and build TSM back-end data structure.

    def __init__(
        self,
        tsm_data: ILATsmData,
        probe_enum_defs: Dict[str, enum.EnumMeta],
        state_names: List[str],
        counter_widths: List[int],
        error_listener: ErrorListener,
    ):
        self._tsm_data: ILATsmData = tsm_data
        self._probe_enum_defs: Dict[str, enum.EnumMeta] = probe_enum_defs
        self._counter_widths: List[int] = counter_widths
        self._error_listener: ILATsmErrorListener = error_listener
        self._state_names: List[str] = state_names
        self._counter_match_check: Dict[int, CounterMatch] = {}
        self._trigger_count: int = 0

    def aggregateResult(self, aggregate, next_result):
        """
        Aggregate results from non-terminal children, when calling self.visitChildren(ctx)
        Default overridden version just returns 'next_result' and does not aggregate.
        """
        if not next_result:
            return aggregate
        if not aggregate:
            return next_result
        if isinstance(aggregate, UserList):
            aggregate.append(next_result)
        else:
            aggregate = UserList([aggregate, next_result])
        return aggregate

    def _verify_counter_match(
        self, ctx: ILATsmParser.Counter_matchContext, cmp: ILATsmCounterCompare
    ):
        def ctx_to_str(ctx0: ILATsmParser.Counter_matchContext) -> str:
            return str(self.visit(ctx0.number()))

        prev: CounterMatch = self._counter_match_check.get(cmp.counter_index, None)
        if prev is None:
            # First found, add it.
            self._counter_match_check[cmp.counter_index] = CounterMatch(ctx, cmp)
            return

        # Compare the binary compare values.
        if prev.cmp.compare_value != cmp.compare_value:
            prev_ctx = prev.ctx.number()
            self._report_error(
                ctx.number(),
                "A counter must use the same compare value in the whole state machine.\n"
                f'The compare value "{ctx_to_str(ctx)}" conflicts with "{ctx_to_str(prev.ctx)}"\n'
                f"at line {prev_ctx.start.line}:{prev_ctx.start.column}.",
            )

    def _report_error(self, ctx: Union[ParserRuleContext, TerminalNodeImpl], msg: str):
        self._error_listener.report_error_ctx(ctx, msg)

    # Visit a parse tree produced by ILATsmParser#ila_tsm.
    def visitIla_tsm(self, ctx: ILATsmParser.Ila_tsmContext):
        tsm_states = self.visitChildren(ctx)
        if not isinstance(tsm_states, Iterable):
            tsm_states = [tsm_states]
        self._tsm_data.states = tsm_states
        select_counter_actions(self._tsm_data)

        if self._error_listener.get_error_count() == 0:
            verify_all_states_visited(tsm_states, self._error_listener)
        if self._trigger_count == 0:
            self._report_error(ctx, "The state machine need at least one trigger action.")

    def visitState_if(self, ctx: ILATsmParser.State_ifContext):
        state = ctx.IDENTIFIER().getText()
        state_index = self._state_names.index(state)
        branch_list = self.visit(ctx.if_condition())
        tsm_state = ILATsmState(state, state_index, branches=branch_list)
        return tsm_state

    def visitState_no_if(self, ctx: ILATsmParser.State_no_ifContext):
        state = ctx.IDENTIFIER().getText()
        state_index = self._state_names.index(state)
        action_block, next_state = self.visit(ctx.actions())
        tsm_branch = ILATsmBranch(
            index=0, actions=action_block, condition=None, next_state=next_state
        )
        tsm_state = ILATsmState(state, state_index, branches=[tsm_branch])
        return tsm_state

    # Visit a parse tree produced by ILATsmParser#if_condition.
    def visitIf_condition(self, ctx: ILATsmParser.If_conditionContext):
        """
        2 conditions, 3 action blocks, for if-then-elsif-then-else
        2 conditions, 2 action blocks, for if_then-elsif-then     (no else branch)
        1 condition,  2 action blocks, for if_then-else
        1 condition,  1 action block , for if_then                (no else branch)
        """

        full_conditions = [self.visit(cond) for cond in ctx.full_condition()]
        # action_blocks_and_next_states are a list of tuples:  [(ILATsmAction, goto_state)]
        action_blocks_and_next_states = [self.visit(action) for action in ctx.actions()]
        action_blocks, next_states = map(list, zip(*action_blocks_and_next_states))

        verify_all_if_condition_counters(ctx, full_conditions, self._error_listener)

        tsm_conditions = [ILATsmCondition.from_item_list(cond) for cond in full_conditions]
        if len(tsm_conditions) == len(action_blocks):
            self._report_error(ctx.actions(len(action_blocks) - 1), "Missing ELSE branch.")
        else:
            # Make all lists the same length.
            tsm_conditions.append(None)

        tsm_branches = [
            ILATsmBranch(index, actions, condition, next_state)
            for index, (actions, condition, next_state) in enumerate(
                zip(action_blocks, tsm_conditions, next_states)
            )
        ]

        return tsm_branches

    # Visit a parse tree produced by ILATsmParser#full_condition.
    def visitFull_condition(self, ctx: ILATsmParser.Full_conditionContext):
        condition_list = self.visitChildren(ctx)
        verify_condition(ctx, condition_list, self._error_listener)
        return condition_list

    # Visit a parse tree produced by ILATsmParser#condition_logic_op.
    def visitCondition_logic_op(self, ctx: ILATsmParser.Condition_logic_opContext):
        # Keep a flat list.
        condition_list = self.visit(ctx.condition(0))
        condition_list.append(ctx.LOGIC_OP().getText())
        condition_list.extend(self.visit(ctx.condition(1)))
        return condition_list

    # Visit a parse tree produced by ILATsmParser#condition_probe_match.
    def visitCondition_probe_match(self, ctx: ILATsmParser.Condition_probe_matchContext):
        return [self.visitChildren(ctx)]

    # Visit a parse tree produced by ILATsmParser#condition_counter_match.
    def visitCondition_counter_match(self, ctx: ILATsmParser.Condition_counter_matchContext):
        return [self.visitChildren(ctx)]

    def visitCondition_paren(self, ctx: ILATsmParser.Condition_parenContext):
        condition_list: list = self.visit(ctx.condition())
        has_counter = any(isinstance(item, ILATsmCounterCompare) for item in condition_list)
        has_probe = any(isinstance(item, ILATsmMatchUnit) for item in condition_list)
        has_parent_op = isinstance(ctx.parentCtx, ILATsmParser.Condition_logic_opContext)
        if has_counter and has_probe and has_parent_op:
            self._report_error(
                ctx,
                "Counter expression can not be together with a probe expression,"
                " inside nested parentheses.",
            )
        return condition_list

    # Visit a parse tree produced by ILATsmParser#probe_match.
    def visitProbe_match(self, ctx: ILATsmParser.Probe_matchContext):
        reverse_order = ctx.getChild(0) is not ctx.IDENTIFIER()
        number = self.visit(ctx.probe_number())
        probe_name = ctx.IDENTIFIER().getText()
        binary_number = "xxx"
        op = ctx.COMPARE_OP().getText()
        probe: ILAProbe = self._tsm_data.probes.get(probe_name, None)
        if not probe:
            self._report_error(ctx, f'Undefined probe: "{probe_name}"')
        else:
            enum_def = self._probe_enum_defs.get(probe_name, None)
            binary_number = verify_tsm_number(
                ctx, probe_name, probe.bit_width, op, number, self._error_listener, enum_def
            )

        return ILATsmMatchUnit(probe, op, binary_number, reverse_order)

    # Visit a parse tree produced by ILATsmParser#counter_match.
    def visitCounter_match(self, ctx: ILATsmParser.Counter_matchContext):
        number = self.visit(ctx.number())
        counter_name, counter_index, bit_width = self.get_counter_info_verify(ctx)
        op = ctx.COMPARE_OP().getText()
        if op not in ["==", "!="]:
            self._report_error(
                ctx,
                f'Operator "{op}" is not allowed in counter compare expressions. '
                'Only operators "==" and "!=" are supported for counters.',
            )

        if bit_width == 0:
            binary_number = "x"
        else:
            binary_number = verify_tsm_number(
                ctx, counter_name, bit_width, op, number, self._error_listener
            )
        cmp = ILATsmCounterCompare(counter_index, op, binary_number)
        self._verify_counter_match(ctx, cmp)
        return cmp

    # Visit a parse tree produced by ILATsmParser#actions.
    def visitActions(self, ctx: ILATsmParser.ActionsContext):
        actions = self.visitChildren(ctx)
        if not isinstance(actions, Iterable):
            actions = [actions]
        verify_action_block(ctx, actions, self._error_listener)
        next_state = 0
        for action in actions:
            if action.name == "goto":
                next_state = action.index
                break
        fsm_action = ILATsmAction.from_action_pair_list(actions)
        return fsm_action, next_state

    # Visit a parse tree produced by ILATsmParser#clear_flag.
    def visitAction_clear_flag(self, ctx: ILATsmParser.Action_clear_flagContext):
        return ILATsmActionPair(_lower(ctx.CLEAR_FLAG()), int(ctx.FLAG_NAME().getText()[-1]))

    # Visit a parse tree produced by ILATsmParser#set_flag.
    def visitAction_set_flag(self, ctx: ILATsmParser.Action_set_flagContext):
        return ILATsmActionPair(_lower(ctx.SET_FLAG()), int(ctx.FLAG_NAME().getText()[-1]))

    # Visit a parse tree produced by ILATsmParser#inc_counter.
    def visitAction_inc_counter(self, ctx: ILATsmParser.Action_inc_counterContext):
        _, counter_index, _2 = self.get_counter_info_verify(ctx)
        return ILATsmActionPair(_lower(ctx.INCREMENT_COUNTER()), counter_index)

    # Visit a parse tree produced by ILATsmParser#reset_counter.
    def visitAction_reset_counter(self, ctx: ILATsmParser.Action_reset_counterContext):
        _, counter_index, _2 = self.get_counter_info_verify(ctx)
        return ILATsmActionPair(_lower(ctx.RESET_COUNTER()), counter_index)

    # Visit a parse tree produced by ILATsmParser#goto.
    def visitAction_goto(self, ctx: ILATsmParser.Action_gotoContext):
        state_name = ctx.IDENTIFIER().getText()
        state_index = 0
        try:
            state_index = self._state_names.index(state_name)
        except ValueError:
            self._report_error(ctx.IDENTIFIER(), f'Unknown state "{state_name}".')

        return ILATsmActionPair(_lower(ctx.GOTO()), state_index)

    # Visit a parse tree produced by ILATsmParser#trigger.
    def visitAction_trigger(self, ctx: ILATsmParser.Action_triggerContext):
        self._trigger_count += 1
        return ILATsmActionPair(_lower(ctx.TRIGGER()), -1)

    # Visit a parse tree produced by ILATsmParser#enum_val.
    def visitEnum_val(self, ctx: ILATsmParser.Enum_valContext):
        return ctx.ENUM_VAL().getText()

    # Visit a parse tree produced by ILATsmParser#enum_string_val.
    def visitEnum_string_val(self, ctx: ILATsmParser.Enum_string_valContext):
        return ctx.ENUM_STRING_VAL().getText()

    # Visit a parse tree produced by ILATsmParser#int_val.
    def visitInt_val(self, ctx: ILATsmParser.Int_valContext):
        return ctx.INTEGER_VAL().getText()

    # Visit a parse tree produced by ILATsmParser#hex_val.
    def visitHex_val(self, ctx: ILATsmParser.Hex_valContext):
        return ctx.HEX_VAL().getText()

    # Visit a parse tree produced by ILATsmParser#bin_val.
    def visitBin_val(self, ctx: ILATsmParser.Bin_valContext):
        return ctx.BINARY_VAL().getText()

    def get_counter_info_verify(self, ctx) -> (str, int, int):
        counter_name = ctx.COUNTER_NAME().getText().upper()
        counter_index = int(counter_name[-1])
        bit_width = self._counter_widths[int(counter_index)]
        if bit_width == 0:
            self._report_error(ctx, f"{counter_name} is not supported by the ILA core.")
        return counter_name, counter_index, bit_width


def _lower(ctx: ParserRuleContext) -> str:
    return ctx.getText().lower()


def verify_all_states_visited(
    tsm_states: List[ILATsmState],
    error_listener: ILATsmErrorListener,
    visited_states: Set[int] = None,
    state_index: int = 0,
):
    if not tsm_states or state_index < 0 or state_index >= len(tsm_states):
        return
    if visited_states is None:
        visited_states = set()
    if state_index in visited_states:
        return

    visited_states.add(state_index)

    for branch in tsm_states[state_index].branches:
        if branch.next_state is not None:
            verify_all_states_visited(tsm_states, error_listener, visited_states, branch.next_state)

    if state_index == 0 and len(tsm_states) > len(visited_states):
        all_states = set(range(len(tsm_states)))
        unreached_states = all_states.difference(visited_states)
        unreached_state_names = ", ".join(
            tsm_states[index].name for index in sorted(unreached_states)
        )
        error_listener.report_error(
            None, None, f"The following states are not reachable: {unreached_state_names}."
        )


def verify_action_block(
    ctx: ILATsmParser.ActionsContext,
    actions: List[ILATsmActionPair],
    error_listener: ILATsmErrorListener,
):
    # Dict key is flag index or counter index.
    flags = defaultdict(list)
    counters = defaultdict(list)
    gotos = []
    trigger_count = 0

    for action in actions:
        if action.name == "trigger":
            trigger_count += 1
        elif action.name == "goto":
            gotos.append(action.index)
        elif action.name in ["set_flag", "clear_flag"]:
            flags[action.index].append(action.name)
        elif action.name in ["decrement_counter", "increment_counter", "reset_counter"]:
            counters[action.index].append(action.name)

    if len(gotos) > 1:
        error_listener.report_error_ctx(
            ctx, "Multiple GOTO statements are not allowed, in same the action block."
        )
    elif len(gotos) == 1 and actions[-1].name != "goto":
        error_listener.report_error_ctx(
            ctx, "The GOTO action must be the last action, in the action block."
        )
    elif len(gotos) + trigger_count != 1:
        error_listener.report_error_ctx(
            ctx, "An action block must have one GOTO action or one TRIGGER action."
        )

    if trigger_count > 1:
        error_listener.report_error_ctx(
            ctx, "Only one TRIGGER action is allowed in each action block."
        )

    for index, actions in flags.items():
        if len(actions) > 1:
            error_listener.report_error_ctx(
                ctx, f"$FLAG{index} may only have one action in each action block."
            )

    for index, actions in counters.items():
        if len(actions) > 1:
            error_listener.report_error_ctx(
                ctx, f"$COUNTER{index} may only have one action in each action block."
            )


def verify_condition(
    ctx: ILATsmParser.Full_conditionContext,
    condition_list: list,
    error_listener: ILATsmErrorListener,
):
    """
    Make sure
        - Only one counter, and the counter is first or last in the list.
        - Operators between probes are identical.
    Args:
        ctx (): parser tree node, has location used for error reporting.
        condition_list (): List made up of "||", "&&", ILATsmMatchUnit, ILATsmCounterCompare.
            Every 2nd item in the list is an operator.
        error_listener ():
    """
    counters = [isinstance(item, ILATsmCounterCompare) for item in condition_list]
    counter_count = counters.count(True)
    if counter_count > 1:
        error_listener.report_error_ctx(
            ctx, "Only one counter match comparison is allowed in a condition."
        )
    elif counter_count == 1 and len(condition_list) > 3 and not counters[0] and not counters[-1]:
        # if list is <= 3, the counter is in first or last position.
        error_listener.report_error_ctx(
            ctx, "Counter match comparison must be either first or last in a condition."
        )

    probe_ops = set()
    cl = condition_list
    for idx in range(1, len(cl), 2):
        if isinstance(cl[idx - 1], ILATsmMatchUnit) and isinstance(cl[idx + 1], ILATsmMatchUnit):
            probe_ops.add(cl[idx])

    if len(probe_ops) > 1:
        op_str = ", ".join(sorted(probe_ops))
        error_listener.report_error_ctx(
            ctx,
            "Different logic operator are not allowed between probe match comparisons,"
            " within an if-condition branch. "
            f"These operators are used: {op_str}.",
        )


def verify_all_if_condition_counters(
    ctx: ParserRuleContext, conditions: Union[list, Any], error_listener: ILATsmErrorListener
):
    # Verify only one counter is used in all conditions for one state.
    # in_conditions may be a list or a list of lists.
    counters_found = set()

    def find_counters(condition: Union[list, Any]):
        if isinstance(condition, ILATsmCounterCompare):
            counters_found.add(condition.counter_index)
        elif isinstance(condition, list):
            for item in condition:
                find_counters(item)

    find_counters(conditions)
    if len(counters_found) > 1:
        counters_str = ", ".join(f"$COUNTER{idx}" for idx in counters_found)
        error_listener.report_error_ctx(
            ctx,
            f'These counters "{counters_str}" are used in match expressions, in the same state. '
            "Only one counter may be used in the same state.",
        )


def verify_tsm_number(
    ctx: ParserRuleContext,
    name: str,
    bit_width: int,
    op: str,
    value: str,
    error_listener: ILATsmErrorListener,
    enum_def: Optional[enum.EnumMeta] = None,
) -> str:
    """Verify correctness of number and return binary value string."""

    number_error_count = 0

    def report_number(msg: str):
        nonlocal number_error_count
        error_listener.report_error_ctx(ctx, msg)
        number_error_count += 1

    def split_value_str(val: str) -> (int, str, str):
        q_pos = val.index("'")
        type_ch = val[q_pos + 1 : q_pos + 2].upper()
        width_prefix = int(val[:q_pos]) if q_pos > 0 else bit_width
        # Remove any quotes around enum value.
        number = val[q_pos + 2 :].strip('"')
        return width_prefix, type_ch, number

    def get_hex_char_bit_len(ch: str) -> int:
        if ch in "x01":
            return 1
        elif ch in "23":
            return 2
        elif ch in "4567":
            return 3
        else:
            return 4

    def verify_int_value(number: Union[str, int]) -> str:
        if isinstance(number, str):
            # Python string ints may use "_" between digits, but not in the first or last positions.
            int_value = int(number.strip("_"))
        else:
            int_value = number
        val_len = int.bit_length(int_value)
        if val_len > bit_width:
            report_number(
                f'"{name}" has bit width:{bit_width} and cannot be assigned'
                f' value "{number}" which has bit width:{val_len}.'
            )
            return None

        return f"{int_value:0{bit_width}b}"

    def verify_enum_value(number: str) -> str:
        # Only probes can have enum values. Grammar makes sure counter names are not using enum values.
        res = None
        if not enum_def:
            report_number(f'"Probe {name}" does not support enum values.')
        else:
            try:
                enum_int_val = enum_def[number].value
            except KeyError:
                report_number(f'Probe "{name}" does not have enum value "{number}" defined.')
            else:
                res = verify_int_value(enum_int_val)
        return res

    def verify_hex_value(hex_number: str):
        valid_hex_chars = "x0123456789abcdef_"
        value_no_underscore = "".join([ch for ch in hex_number.lower() if ch != "_"])
        hex_val_len = len(value_no_underscore)
        if hex_val_len == 0:
            report_number(f'"{name}" is assigned an invalid value "{hex_number}".')
            return None
        if not all([ch in valid_hex_chars for ch in value_no_underscore]):
            report_number(
                f'"{name}" value "{hex_number}" has invalid character(s).'
                f' Valid characters are {valid_hex_chars}".'
            )
            return None

        required_hex_ch_len = (bit_width + 3) // 4
        bin_val_len = (hex_val_len - 1) * 4 + get_hex_char_bit_len(value_no_underscore[0])
        if hex_val_len != required_hex_ch_len:
            report_number(
                f'"{name}" has bit width:{bit_width} requiring {required_hex_ch_len} hex character(s)'
                f' but value "{hex_number}" has {hex_val_len} hex character(s).'
            )
        elif bin_val_len > bit_width:
            # Too many bits in first hex char.
            report_number(
                f'"{name}" has bit width:{bit_width} and cannot be assigned'
                f' value "{hex_number}" which has bit width:{bin_val_len}.'
            )
        if (op not in ["==", "!="]) and ("x" in value_no_underscore):
            report_number(
                f'"{name}" is assigned value "{op} {hex_number}". '
                f"""The operator cannot be used when the value has a don't care "x"."""
            )
        return hex_to_bin_str(value_no_underscore, bit_width)

    def verify_bin_value(bin_number):
        # binary value
        bad_chars = set(bin_number) - set(ILA_MATCH_BIT_VALUES)
        if bad_chars:
            bad_char_str = "".join([ch for ch in bad_chars])
            report_number(
                f'"{name}" value "{bin_number}" has invalid character(s): "{bad_char_str}".'
                f' Valid characters are "{ILA_MATCH_BIT_VALUES}".'
            )
            return None

        value_no_underscore = "".join([ch for ch in bin_number.lower() if ch != "_"])
        val_len = len(value_no_underscore)
        if val_len != bit_width:
            report_number(
                f'"{name}" has bit width:{bit_width} and cannot be assigned'
                f' value "{bin_number}" which has bit width:{val_len}.'
            )
        if (op not in ["==", "!="]) and not all([ch in "01_" for ch in bin_number]):
            report_number(
                f'"{name}" is assigned value "{op} {bin_number}". '
                f'The operator "{op}" can only be used with "0" and "1" bit values.'
            )
        return value_no_underscore

    # Value has 3 parts <length prefix> <type char> <number>
    value_width, value_type_ch, value_number = split_value_str(value)

    if value_width <= 0 or value_width != bit_width:
        report_number(
            f'"{name}" is "{bit_width}" bits wide, but value "{value}" length prefix is "{value_width}".'
        )

    if op not in ILA_MATCH_OPERATORS:
        report_number(
            f'"{name}" uses operator "{op}" which is not one of the allowed operators: '
            f"{ILA_MATCH_OPERATORS}."
        )

    if bit_width == 1 and op not in ["==", "!="]:
        report_number(
            f'Operator "{op}" cannot be used for "{name}" which is 1 bit wide. '
            'Only operators "==" and "!=" are allowed.'
        )

    binary_result = None
    if number_error_count:
        binary_result = None
    elif value_type_ch == "U":
        binary_result = verify_int_value(value_number)
    elif value_type_ch == "E":
        binary_result = verify_enum_value(value_number)
    elif value_type_ch == "H":
        binary_result = verify_hex_value(value_number)
    elif value_type_ch == "B":
        binary_result = verify_bin_value(value_number)

    if number_error_count or binary_result is None:
        return "x" * bit_width
    else:
        return binary_result
