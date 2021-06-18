..
  Copyright 2021 Xilinx, Inc.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

======================
ChipScoPy Overview
======================

ChipScoPy is an open-source Python project that enables communication with and control of Xilinx Versal HW debug
solutions. Users are able to program designs and begin debugging in a few simple steps. Client Python scripts have
access to a rich API for hardware interaction. The main features of the ChipScoPy package are:

- Device detection, programming, and status
- Memory subsystems support
- Fabric Debug Core support
   - Integrated Logic Analyzer (ILA)
   - Virtual Input Output (VIO)
- Hardened Core support
   - DDR Memory Controller (DDRMC)
   - Integrated Bit Error Ratio Tester (IBERT)
   - System Monitor (SysMon)
   - Network on Chip Performance Monitor (NoC PerfMon)
   - PCI Express (PCIe)
