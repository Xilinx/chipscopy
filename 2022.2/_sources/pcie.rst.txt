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

PCIe
====

The PCIe debug core is an optional addition to the Versal CPM PCIe functionality, or an
optional addition to the Versal Soft PCIe core.  When included, PCIe debug will track
transitions on the Link Training and Status State Machine (LTSSM), and make that trace
and associated statistics available though properties on the PCIe object.

.. toctree::
   :maxdepth: 3

   pcie/pcie.rst
   pcie/references.rst