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

RX
==

.. py:currentmodule:: chipscopy.api.ibert

**--> ADD GENERAL RX INFO HERE <--**

Reset
-----

To reset the ``RX``, use the :py:meth:`~rx.RX.reset` method

.. code-block:: python
    :emphasize-lines: 12

    # Get all IBERT cores in the device and select the first IBERT core for use
    iberts = device.ibert_cores
    ibert_0 = ibert.at(index=0)

    # Get all the GT Groups in the IBERT core
    all_gt_groups = ibert_0.gt_groups

    # Get the first GT Group and the first GT in the GT Group
    first_gt_group = all_gt_groups.at(index=0)
    first_gt = first_gt_group.gts.at(index=0)

    first_gt.rx.reset()

Attributes of RX object
-----------------------

The attributes of the :py:class:`~rx.RX` class instance are listed here and are accessible via the python
``.`` operator i.e. ``<rx_obj>.<attribute>``.


.. list-table:: RX attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~rx.RX.name`
      - Name of the RX
    * - :py:data:`~rx.RX.type`
      - Serial object type. This is always equal to :py:data:`~aliases.RX_KEY`
    * - :py:data:`~rx.RX.handle`
      - Handle of the RX from cs_server
    * - :py:data:`~rx.RX.pll`
      - PLL driving this RX
    * - :py:data:`~rx.RX.link`
      - :py:class:`~link.Link` for the RX, if any
    * - :py:data:`~rx.RX.eye_scan`
      - :py:class:`~eye_scan.EyeScan` for the RX, if any
    * - :py:data:`~rx.RX.eye_scan_names`
      - Name of all scans run on the RX. This can be used to get the :py:class:`~eye_scan.EyeScan` object for old scans
