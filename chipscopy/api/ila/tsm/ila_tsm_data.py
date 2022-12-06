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
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from functools import reduce
from io import TextIOBase
from typing import List, Dict, Optional, Union

from antlr4 import ParserRuleContext
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Tree import TerminalNodeImpl

from chipscopy.api.ila import ILAPort, ILAProbe


class ILATsmErrorListener(ErrorListener):
    def __init__(self, out_stream: TextIOBase = sys.stderr):
        self._out_stream: TextIOBase = out_stream
        self._error_count = 0

    def get_error_count(self) -> int:
        return self._error_count

    def syntaxError(self, recognizer, offending_symbol, line, column, msg, e):
        self.report_error(line, column, msg)

    def report_error(self, line, column, msg):
        self._error_count += 1
        if line is None or column is None:
            print(msg, file=self._out_stream)
        else:
            print("[Line " + str(line) + ":" + str(column) + "] " + msg, file=self._out_stream)

    def report_error_ctx(self, ctx: Union[ParserRuleContext, TerminalNodeImpl], msg: str):
        if isinstance(ctx, ParserRuleContext):
            self.syntaxError(None, None, ctx.start.line, ctx.start.column, msg, None)
        else:
            self.syntaxError(None, None, ctx.symbol.line, ctx.symbol.column, msg, None)


# TSM constants
COUNTER_COUNT = 4
TABLE_ROWS_PER_STATE = 8
MAX_STATE_COUNT = 16
MAX_BRANCH_COUNT_PER_STATE = 3
MAX_CONDITION_COUNT_PER_STATE = MAX_BRANCH_COUNT_PER_STATE - 1


@dataclass
class ILATsmActionPair:
    name: str
    index: int

    def __str__(self):
        return self.name + str(self.index)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.name == other.name and self.index == other.index


class ILATsmInput(IntEnum):
    CUR_STATE_3 = 6
    CUR_STATE_2 = 5
    CUR_STATE_1 = 4
    CUR_STATE_0 = 3

    IF_COND_MUX = 2
    ELSE_IF_MUX = 1

    COUNTER_CMP_MUX = 0

    NUM_INPUTS = 7


class ILATsmAction(enum.Flag):
    # FSM ILA core register action encoding.
    DEFAULT = 0x00_0000

    GOTO_0 = 0x00_0001
    GOTO_1 = 0x00_0002
    GOTO_2 = 0x00_0004
    GOTO_3 = 0x00_0008

    RESET_COUNTER_0 = 0x00_0010
    INCREMENT_COUNTER_0 = 0x00_0020

    RESET_COUNTER_1 = 0x00_0040
    INCREMENT_COUNTER_1 = 0x00_0080

    RESET_COUNTER_2 = 0x00_0100
    INCREMENT_COUNTER_2 = 0x00_0200

    RESET_COUNTER_3 = 0x00_0400
    INCREMENT_COUNTER_3 = 0x00_0800

    SELECT_COUNTER_1_OR_3 = 0x00_1000
    SELECT_COUNTER_2_OR_3 = 0x00_2000

    SET_FLAG_0 = 0x00_4000
    SET_FLAG_1 = 0x00_8000
    SET_FLAG_2 = 0x01_0000
    SET_FLAG_3 = 0x02_0000

    CAPTURE = 0x04_0000  # Not supported
    TRIGGER = 0x08_0000

    CLEAR_FLAG_0 = 0x10_0000
    CLEAR_FLAG_1 = 0x20_0000
    CLEAR_FLAG_2 = 0x40_0000
    CLEAR_FLAG_3 = 0x80_0000

    @staticmethod
    def create(action: ILATsmActionPair):
        if action.name == "goto":
            val = action.index
        elif action.name == "reset_counter":
            val = ILATsmAction.RESET_COUNTER_0.value << (action.index * 2)
        elif action.name == "increment_counter":
            val = ILATsmAction.INCREMENT_COUNTER_0.value << (action.index * 2)
        elif action.name == "set_flag":
            val = ILATsmAction.SET_FLAG_0.value << action.index
        elif action.name == "clear_flag":
            val = ILATsmAction.CLEAR_FLAG_0.value << action.index
        elif action.name == "trigger":
            val = ILATsmAction.TRIGGER.value
        else:
            val = 0
        return ILATsmAction(val)

    @staticmethod
    def from_action_pair_list(actions: List[ILATsmActionPair]):
        fsm_actions = map(ILATsmAction.create, actions)
        combined_actions = reduce((lambda x, y: x | y), fsm_actions)
        return combined_actions

    @staticmethod
    def add_select_counter_action(action, counter_index: int):
        """
        Adds to input "action" value the select_counter actions corresponding to "counter_index".
        Args:
            action (ILATsmAction): Old action value.
            counter_index (int): Counter index corresponding to the next state.

        Returns: New action object which has input "action" actions plus SELECT_COUNTER actions.

        """
        val = action.value
        if counter_index == 1 or counter_index == 3:
            val |= ILATsmAction.SELECT_COUNTER_1_OR_3.value
        if counter_index == 2 or counter_index == 3:
            val |= ILATsmAction.SELECT_COUNTER_2_OR_3.value
        return ILATsmAction(val)

    def dump(self) -> str:
        ITA = ILATsmAction
        goto_state = self.value & 0xF
        select_counter = 1 if ITA.SELECT_COUNTER_1_OR_3 in self else 0
        select_counter += 2 if ITA.SELECT_COUNTER_2_OR_3 in self else 0
        mask = (
            ITA.SELECT_COUNTER_1_OR_3
            | ITA.SELECT_COUNTER_2_OR_3
            | ITA.GOTO_0
            | ITA.GOTO_1
            | ITA.GOTO_2
            | ITA.GOTO_3
        )
        aa = ILATsmAction(self.value & ~mask.value)
        s = str(aa) + f"|SEL_C:{select_counter}|GOTO:{goto_state}"
        # Clean up string.
        s = s.replace("FLAG_", "F:")
        s = s.replace("COUNTER_", "C:")
        s = s.replace("ILATsmAction.", "")
        s = s.replace("DEFAULT", "")
        s = s.replace("INCREMENT", "INC")
        s = s.replace("|", " ")

        bin_value = f"{self.value:024b}"
        bin_value = "_".join(bin_value[idx : idx + 4] for idx in range(0, len(bin_value), 4))

        return bin_value + " " + s.lower()


@dataclass
class ILATsmCounterCompare:
    counter_index: int
    compare_op: str
    compare_value: str

    def __str__(self):
        return f"$COUNTER{self.counter_index} {self.compare_op} {self.compare_value}"

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return (
            self.counter_index == other.counter_index
            and self.compare_op == other.compare_op
            and self.compare_value == other.compare_value
        )


@dataclass
class ILATsmMatchUnit:
    # Reverse order example: "16'H0004 <= probe_a", instead of "probe_a > 16'H0004"
    probe: ILAProbe
    compare_op: str
    compare_value: str
    reverse_order: bool

    def get_compare_operator(self) -> str:
        return reverse_compare_operator(self.compare_op) if self.reverse_order else self.compare_op


@dataclass
class ILATsmCondition:
    probe_operator: Optional[str]
    counter_operator: Optional[str]
    counter_compare: Optional[ILATsmCounterCompare]
    match_units: List[ILATsmMatchUnit] = field(default_factory=lambda: [])

    def is_invert_counter_mux(self) -> bool:
        return self.counter_compare and self.counter_compare.compare_op == "!="

    def get_mapper_probe_operator(self) -> str:
        # "and" is default value.
        return "or" if self.probe_operator == "||" else "and"

    @staticmethod
    def from_item_list(condition_list: List[Union[str, ILATsmMatchUnit, ILATsmCounterCompare]]):
        """condition_list (): List made up of "||", "&&", ILATsmMatchUnit, ILATsmCounterCompare."""
        probe_op, counter_op, counter_compare = None, None, None
        if len(condition_list) == 1:
            # Handle single ILATsmCounterCompare item.
            # Single ILATSmMatchUnit item case is handled by collecting "mus" below.
            if isinstance(condition_list[0], ILATsmCounterCompare):
                counter_compare = condition_list[0]
        else:
            for op_idx in range(1, len(condition_list), 2):
                pre = condition_list[op_idx - 1]
                op = condition_list[op_idx]
                post = condition_list[op_idx + 1]
                if isinstance(pre, ILATsmCounterCompare):
                    counter_op = op
                    counter_compare = pre
                elif isinstance(post, ILATsmCounterCompare):
                    counter_op = op
                    counter_compare = post
                elif isinstance(pre, ILATsmMatchUnit) and isinstance(post, ILATsmMatchUnit):
                    probe_op = op

        mus = list(filter(lambda x: isinstance(x, ILATsmMatchUnit), condition_list))
        return ILATsmCondition(probe_op, counter_op, counter_compare, mus)


@dataclass
class ILATsmBranch:
    index: int
    actions: ILATsmAction
    condition: Optional[ILATsmCondition]
    next_state: int


@dataclass
class ILATsmState:
    name: str
    index: int
    counter_index: int = 0
    branches: List[ILATsmBranch] = field(default_factory=lambda: [])


@dataclass
class ILATsmData:
    name: str
    ports: List[ILAPort]
    probes: Dict[str, ILAProbe]
    counter_widths: List[int]
    states: List[ILATsmState] = field(default_factory=lambda: [])

    def get_match_unit_count(self):
        return sum(len(port.match_units) for port in self.ports)


def reverse_compare_operator(op: str) -> str:
    """
    Return operator when reversing order of operands.
    E.g.  16'h4000 < $counter3 => $counter3 >= 16'h4000
    """
    reverse = {">": "<=", "<": ">=", ">=": "<", "<=": ">"}
    # For "==" and "!=", the reverse is the same as the passed in operator.
    return reverse.get(op, op)
