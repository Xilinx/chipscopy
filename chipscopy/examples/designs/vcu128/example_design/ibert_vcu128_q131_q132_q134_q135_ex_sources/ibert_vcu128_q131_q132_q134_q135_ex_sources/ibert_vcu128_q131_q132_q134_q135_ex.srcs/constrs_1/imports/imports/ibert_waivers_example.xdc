# Copyright (C) 2024, Advanced Micro Devices, Inc.
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

############################################################


############################################################



create_waiver -internal -quiet -type CDC -id {CDC-1} -user ibert_ultrascale_gty -tags "1165692" -description "CDC-1 waiver for CPLL Calibration logic" \
                        -scope -from [get_ports {gty_refclk*p_i[*]}] \
						       -to [get_pins -quiet -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {NAME =~*QUAD*.u_q/u_common/U_COMMON_REGS/reg_*/I_EN_STAT_EQ1.U_STAT/xsdb_reg_reg[*]}]]



