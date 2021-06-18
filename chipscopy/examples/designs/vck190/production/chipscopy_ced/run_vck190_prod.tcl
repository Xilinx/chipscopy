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

create_project xpr_vck190_prod ./xpr_vck190_prod -part xcvc1902-vsva2197-2MP-e-S
set_property board_part xilinx.com:vck190:part0:2.2 [current_project]
import_files -fileset constrs_1 -force -norecurse {./versal_ibert.xdc}
set_property target_constrs_file [get_files ./xpr_vck190_prod/xpr_vck190_prod.srcs/constrs_1/imports/src/versal_ibert.xdc] [current_fileset -constrset]
#set_property used_in_synthesis false [get_files ./xpr_vck190_prod/xpr_vck190_prod.srcs/constrs_1/imports/src/versal_ibert.xdc]

source ./chipscopy_ex_bd_vck190_prod.tcl

make_wrapper -files [get_files ./xpr_vck190_prod/xpr_vck190_prod.srcs/sources_1/bd/chipscopy_ex/chipscopy_ex.bd] -top
add_files -norecurse ./xpr_vck190_prod/xpr_vck190_prod.gen/sources_1/bd/chipscopy_ex/hdl/chipscopy_ex_wrapper.v
update_compile_order -fileset sources_1

