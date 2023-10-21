# Generated from ILATsm.g4 by ANTLR 4.10.1
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .ILATsmParser import ILATsmParser
else:
    from ILATsmParser import ILATsmParser

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


# This class defines a complete generic visitor for a parse tree produced by ILATsmParser.


class ILATsmVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by ILATsmParser#ila_tsm.
    def visitIla_tsm(self, ctx: ILATsmParser.Ila_tsmContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#state_if.
    def visitState_if(self, ctx: ILATsmParser.State_ifContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#state_no_if.
    def visitState_no_if(self, ctx: ILATsmParser.State_no_ifContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#if_condition.
    def visitIf_condition(self, ctx: ILATsmParser.If_conditionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#actions.
    def visitActions(self, ctx: ILATsmParser.ActionsContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#full_condition.
    def visitFull_condition(self, ctx: ILATsmParser.Full_conditionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#condition_counter_match.
    def visitCondition_counter_match(self, ctx: ILATsmParser.Condition_counter_matchContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#condition_paren.
    def visitCondition_paren(self, ctx: ILATsmParser.Condition_parenContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#condition_logic_op.
    def visitCondition_logic_op(self, ctx: ILATsmParser.Condition_logic_opContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#condition_probe_match.
    def visitCondition_probe_match(self, ctx: ILATsmParser.Condition_probe_matchContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#probe_match.
    def visitProbe_match(self, ctx: ILATsmParser.Probe_matchContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#counter_match.
    def visitCounter_match(self, ctx: ILATsmParser.Counter_matchContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#action_clear_flag.
    def visitAction_clear_flag(self, ctx: ILATsmParser.Action_clear_flagContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#action_set_flag.
    def visitAction_set_flag(self, ctx: ILATsmParser.Action_set_flagContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#action_inc_counter.
    def visitAction_inc_counter(self, ctx: ILATsmParser.Action_inc_counterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#action_reset_counter.
    def visitAction_reset_counter(self, ctx: ILATsmParser.Action_reset_counterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#action_goto.
    def visitAction_goto(self, ctx: ILATsmParser.Action_gotoContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#action_trigger.
    def visitAction_trigger(self, ctx: ILATsmParser.Action_triggerContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#probe_val.
    def visitProbe_val(self, ctx: ILATsmParser.Probe_valContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#enum_val.
    def visitEnum_val(self, ctx: ILATsmParser.Enum_valContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#enum_string_val.
    def visitEnum_string_val(self, ctx: ILATsmParser.Enum_string_valContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#int_val.
    def visitInt_val(self, ctx: ILATsmParser.Int_valContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#hex_val.
    def visitHex_val(self, ctx: ILATsmParser.Hex_valContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ILATsmParser#bin_val.
    def visitBin_val(self, ctx: ILATsmParser.Bin_valContext):
        return self.visitChildren(ctx)


del ILATsmParser
