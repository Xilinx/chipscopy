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

VIO
===

VIO is a customizable core that can monitor and drive internal FPGA signals in real time. VIO inputs and
outputs can be monitored and controlled from the ChipScoPy VIO API.

.. image:: images/vio_bd_instance.png
   :scale: 70%
   :align: center

In the picture above, there is 1 input port and 5 output ports. The input is connected to a bus in the design to
monitor. The probe outputs are virtual buttons that connect to design components to control.

Details
-------

VIO Inputs
^^^^^^^^^^
Inputs to the VIO are driven by the user design. The input values are a snapshot at any given time of the user design
logic. Software is slower to reading values than to the speed of the design, so values may change many times between
API port value reading. Activity detectors report changes to the VIO port inputs between software reads.

VIO Input Activity Detectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A VIO core input optionally has additional cells to capture the presence of transitions on the input. Because the design
clock is most likely much faster than the sample period of the Analyzer, it is possible for the signal being monitored
to transition many times between successive samples. The activity detectors capture this behavior and the results are
returned with the port values.

VIO Outputs
^^^^^^^^^^^
Outputs from the VIO are driven to the surrounding user design. The output values are driven to 1s and 0s by the
ChipScoPy API. Initial output values are set to desired values during IP generation time.

VIO output ports follow a naming convention "probe_out<#>[x:y]" where <#> is an index from 0-1023, and [x:y] is the
bit width.

VIO Probes
^^^^^^^^^^
There is a logical mapping between ports of a VIO core and elements in the user's design. This port mapping is recorded
in the LTX file in the Vivado design flow.

When an LTX file is read, the HDL net/bus name mapping is available. This enables reading and writing probe values in
the context of the HDL design.

For example, if an HDL design mapped "counter[31:0]" to a VIO input port 0, ``read_probes("counter")`` returns the
value of the counter attached to that VIO input. This is equivalent to ``read_ports("probe0_in")``, but allows
you to identify nets in the context of the source HDL design.


VIO API Reference
^^^^^^^^^^^^^^^^^

VIO Class
"""""""""
.. autoclass:: chipscopy.api.vio.VIO
    :members:


VIOProbe Class
""""""""""""""
.. autoclass:: chipscopy.api.vio.VIOProbe
    :members:
