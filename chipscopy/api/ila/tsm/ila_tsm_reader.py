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
import enum
from io import TextIOBase, StringIO
from typing import List, Dict, Union, Optional
from antlr4 import CommonTokenStream, FileStream, InputStream

from chipscopy.api.ila.tsm.ILATsmLexer import ILATsmLexer
from chipscopy.api.ila.tsm.ILATsmParser import ILATsmParser
from chipscopy.api.ila.tsm.ILATsmVisitor import ILATsmVisitor
from chipscopy.api.ila.tsm.ila_tsm_data import ILATsmData, ILATsmErrorListener, MAX_STATE_COUNT
from chipscopy.api.ila.tsm.ila_tsm_checker import ILATsmCheckAndBuild
from chipscopy.api.ila import ILAPort, ILAProbe
from chipscopy.api.ila.tsm.ila_tsm_mapper import map_tsm_to_props


class ILATsmReader:
    def __init__(
        self,
        input_text: Union[TextIOBase, str],
        ports: List[ILAPort],
        probes: Dict[str, ILAProbe],
        probe_enum_def: Dict[str, enum.EnumMeta],
        counter_bit_widths: List[int],
        has_basic_capture_control: bool = False,
    ):
        self._mapper = None
        self._input = input_text
        self._input_stream: InputStream = None
        self._ports: List[ILAPort] = ports
        self._probes: Dict[str, ILAProbe] = probes
        self._probe_enum_defs: Dict[str, enum.EnumMeta] = probe_enum_def
        self._counter_bit_widths: List[int] = counter_bit_widths
        self._error_string: StringIO = StringIO()
        self._error_listener: ILATsmErrorListener = ILATsmErrorListener(self._error_string)
        self._has_basic_capture_control = has_basic_capture_control
        self._state_names: Dict[int, str] = {}

    def get_error_count(self):
        return self._error_listener.get_error_count()

    def get_error_str(self):
        return self._error_string.getvalue()

    def get_state_names(self) -> Dict[int, str]:
        return self._state_names if self.get_error_count() == 0 else {}

    def parse(self, compile_only: bool = False) -> (int, str, Optional[dict]):
        """

        Args:
            compile_only (bool): If True, the ILA core register values are not generated.

        Returns: (error_count, error_message, register settings).
            register setting will be None if error_count > 0 or compile_only is True.
        """

        tsm_data = None
        state_names = []
        if isinstance(self._input, TextIOBase):
            self._input_stream = InputStream(self._input.read())
        else:
            self._input_stream = FileStream(self._input)

        # Setup lexer
        lexer = ILATsmLexer(self._input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(self._error_listener)

        # Parsing
        token_stream = CommonTokenStream(lexer)
        parser = ILATsmParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(self._error_listener)
        tree = parser.ila_tsm()
        if self.get_error_count() == 0:
            tsm_data = ILATsmData("", self._ports, self._probes, self._counter_bit_widths)

            # Scan for state names
            state_visitor = ILATsmStateVisitor(self._error_listener)
            state_visitor.visit(tree)
            state_names = state_visitor.get_states()
            if len(state_names) > MAX_STATE_COUNT:
                self._error_listener.report_error(
                    0,
                    0,
                    f"Maximum {MAX_STATE_COUNT} states are allowed. "
                    f"The Trigger State Machine has {len(state_names)} states.",
                )
            self._state_names = {idx: name for idx, name in enumerate(state_names)}

        # Semantic checking and build back-end data structure.
        if self.get_error_count() == 0:
            checker = ILATsmCheckAndBuild(
                tsm_data,
                self._probe_enum_defs,
                state_names,
                self._counter_bit_widths,
                self._error_listener,
            )
            checker.visit(tree)

        props = None
        if not compile_only and self.get_error_count() == 0:
            props = map_tsm_to_props(
                tsm_data, self._has_basic_capture_control, self._error_listener
            )
        return self.get_error_count(), self.get_error_str(), props


class ILATsmStateVisitor(ILATsmVisitor):
    """
    Find state names.
    """

    def __init__(self, error_listener: ILATsmErrorListener):
        self._states = []
        self._error_listener = error_listener

    def get_states(self):
        return self._states

    def _add_state(self, ctx: Union[ILATsmParser.State_ifContext, ILATsmParser.State_no_ifContext]):
        state_name = ctx.IDENTIFIER().getText()
        if state_name in self._states:
            self._error_listener.report_error_ctx(
                ctx, f'Two states have the same name: "{state_name}". State names must be unique.'
            )
        else:
            self._states.append(state_name)

    # Visit a parse tre0e produced by ILATsmParser#state_if.
    def visitState_if(self, ctx: ILATsmParser.State_ifContext):
        self._add_state(ctx)
        return None

    # Visit a parse tree produced by ILATsmParser#state_no_if.
    def visitState_no_if(self, ctx: ILATsmParser.State_no_ifContext):
        self._add_state(ctx)
        return None
