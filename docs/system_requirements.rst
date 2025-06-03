..
   Copyright (C) 2021-2022, Xilinx, Inc.
   Copyright (C) 2022-2024, Advanced Micro Devices, Inc.
   
     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at
   
         http://www.apache.org/licenses/LICENSE-2.0
   
     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

System Requirements
-------------------

Host System Hardware
~~~~~~~~~~~~~~~~~~~~

- Hardware Debug Connection
   - `Xilinx Platform Cable USB II <https://www.xilinx.com/products/boards-and-kits/hw-usb-ii-g.html>`_
   - `Xilinx SmartLynq Data Cable <https://www.xilinx.com/products/boards-and-kits/smartlynq-data-cable.html>`_
   - `Xilinx SmartLynq+ Module <https://www.xilinx.com/products/boards-and-kits/smartlynq-plus.html>`_

.. note:: At this time it is not recommended to run cs_server natively on the SmartLynq+ module!


Host System Software
~~~~~~~~~~~~~~~~~~~~

- Operating System: please refer to `Vivado Design Suite User Guide <https://www.xilinx.com/support/documentation/sw_manuals/xilinx2020_2/ug973-vivado-release-notes-install-license.pdf>`_
- |vivado_v| or newer Xilinx Hardware Server ``hw_server``
- |vivado_v| or newer Xilinx ChipScope Server ``cs_server``
- Python 3.9 or newer
- ChipScoPy Python Package
- ChipScoPy Examples


.. note:: Please see :ref:`chipscopy_installation` for a complete guide to installation.


Network Considerations
~~~~~~~~~~~~~~~~~~~~~~

While ``hw_server``, ``cs_server``, and ChipScoPy can be connected over TCP/IP networks for enhanced flexibility, it is not
recommended that they span large WANs. This can introduce performance issues. Specifically using them over VPN may have
undesirable results.

For best results all servers should be on a local physical LAN, contact your network administrator if you have questions.


Supported Boards
~~~~~~~~~~~~~~~~

The example designs distributed with ChipScoPy are supported for these hardware boards:

.. note::
    Not all examples will be supported on all hardware platforms--due to differences in the silicon.

- VCK190 (Versal AI Core Series Evaluation Board):
   - Versal VC1902 Device
   - `VCK190 product page <https://www.xilinx.com/products/boards-and-kits/vck190.html>`_
- VMK180 (Versal Prime Series Evaluation Board):
   - Versal VM1802 Device
   - `VMK180 product page <https://www.xilinx.com/products/boards-and-kits/vmk180.html>`_
- VPK120 (Versal Premium Series Evaluation Board):
    - Versal VP1202 Device
    - `VPK120 product page <https://www.xilinx.com/products/boards-and-kits/vpk120.html>`_
- VHK158 (Versal HBM Series VHK158 Evaluation Kit):
    - Versal VH1582 Device
    - `VHK158 product page <https://www.xilinx.com/products/boards-and-kits/vhk158.html>`_

User Designs
~~~~~~~~~~~~

ChipScoPy supports user-generated designs targeting any Versal series device. To interact with a user design, first
supply the PDI and LTX files to the programming and discovery routines.

The standard design flow will produce these output products for user-generated projects.

.. figure:: images/chipscopy_vivado.png
    :scale: 100%
    :align: center

    Vivado Design Flow


.. note::
   Certain examples may also require the "hardware hand-off" file or ``<project_name>.hwh`` from the user-generated
   project.
