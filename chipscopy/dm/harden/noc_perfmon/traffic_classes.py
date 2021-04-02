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

import enum


class PerfMonTrafficQOSClass(enum.IntFlag):
    LOW_LATENCY_READ_QOS_CLASS = 0x1
    ISOCHRONOUS_READ_QOS_CLASS = 0x2
    BEST_EFFORT_READ_QOS_CLASS = 0x4
    ISOCHRONOUS_WRITE_QOS_CLASS = 0x8
    BEST_EFFORT_WRITE_QOS_CLASS = 0x10


TC_BEW = PerfMonTrafficQOSClass.BEST_EFFORT_WRITE_QOS_CLASS
TC_BER = PerfMonTrafficQOSClass.BEST_EFFORT_READ_QOS_CLASS
TC_ISOW = PerfMonTrafficQOSClass.ISOCHRONOUS_WRITE_QOS_CLASS
TC_ISOR = PerfMonTrafficQOSClass.ISOCHRONOUS_READ_QOS_CLASS
TC_LLR = PerfMonTrafficQOSClass.LOW_LATENCY_READ_QOS_CLASS
