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

DDR
===
The DDR Memory Controller (DDRMC) is an integrated core in the Versal architecture.
During device configuration, each Memory Controller will calibrate with the external memory devices to ensure
a stable data channel for each byte lane.

The status and result of this memory calibration is accessible from the ChipScoPy DDRMC API.
The majority of data in the DDRMC is related to calibration, which is only run once initially.
Therefore the majority of data in the DDRMC is static and the user should not expect many data changes
when reloading/refreshing DDRMC data, except certain features specifically denoted as post-calibration trackers,
or until the Versal device gets reprogrammed.

.. image:: images/ddrmc_comp.png
   :scale: 80%
   :align: center


Details
-------

Calibration
^^^^^^^^^^^
Calibration involves many stages which are vary dependent on the type of memory interface being used as well as
the memory frequency. These stages align the clock strobes and data for each byte lane, adjusting for
the trace lengths for the given board layout.

Margins
^^^^^^^
The width of the data window (margin) for each byte lane is measured in two stages, one which uses a simple
data pattern and one which uses a more aggressive (complex) data pattern.

If the speed of the memory interface is slow, the complex margin stage may be skipped to save calibration time.
For each stage, the read and write margins for the rising and falling edges of the strobe clock
are measured and reported.

DDRMC Properties
^^^^^^^^^^^^^^^^
For each stage of calibration, registers which store the intermediate and final results are updated.
There are also configuration registers which describe the settings in use for the current memory controller
configuration, and as well as registers dedicated for post-calibration features.

All of these register names and values should be provided by the software in format of DDRMC properties
to Xilinx technical support in the event of calibration failure for troubleshooting.


API Functions
^^^^^^^^^^^^^

.. automodule:: chipscopy.api.ddr.ddr
    :members:
