..
   Copyright (C) 2021-2022, Xilinx, Inc.
   Copyright (C) 2022-2026, Advanced Micro Devices, Inc.

     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

JTAG
====

Cable options such as the TCK clock frequency are read and written through
:class:`~chipscopy.api.cable.Cable`. Low-level TAP shift sequences are built with
:class:`~chipscopy.api.jtag.JtagSequence`.

.. warning::
   Cable options are hw_server state shared by every connected client, and they persist
   for the life of the hw_server process. A change made by one session is visible to
   every other session and survives session close. Always restore the original value.

   Changing an option is not synchronized with other traffic on the cable. The caller
   is responsible for not retuning a cable while it is in active use elsewhere, for
   example a live ILA capture or a PDI program.

``frequency`` is quantized to what the cable hardware can generate, and
``frequency_list`` is advisory only at this level: hw_server accepts values outside
the list and snaps them to the nearest achievable rate rather than rejecting them.
Vivado's ``set_property PARAM.FREQUENCY <hz> [current_hw_target]`` reaches the same
underlying option, but the two surfaces are **not** interchangeable. Vivado models
``PARAM.FREQUENCY`` as an enum whose members are the ``frequency_list`` values, so it
validates against the list where hw_server does not, and it caches the value it
requested rather than rereading it, so a value read back through ``ChipScoPy`` can
disagree with what Vivado reports for the same cable.

Reaching a cable
----------------

An ordinary session with no ``cs_server_url`` is the cheapest safe recipe::

    from chipscopy import create_session

    session = create_session(hw_server_url="TCP:my-host:3121")
    cable = session.cables.get(Serial="252502174339A")

    original = cable.get_option("frequency")
    try:
        cable.set_option("frequency", 3_000_000)
        ...  # slow the clock for a marginal-signal experiment
    finally:
        cable.set_option("frequency", original)

Do not reach for ``initial_device_scan=False`` as an optimization. It saves very little,
and it skips the cable-readiness wait, because ``wait_for_all_cables_ready`` is only
called from ``Session.scan_devices``.

Cable
-----

.. autoclass:: chipscopy.api.cable.Cable
    :members:

JTAG sequences
--------------

.. automodule:: chipscopy.api.jtag
    :members:
