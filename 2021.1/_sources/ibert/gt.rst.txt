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

GT
==

.. py:currentmodule:: chipscopy.api.ibert

A GT object represents each individual transceiver in HW. It also includes TX and RX objects as it's children.

Reset
-----

To reset the ``RX`` and ``TX`` in the GT, use the :py:meth:`~gt.GT.reset` method

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
    
    first_gt.reset()

Attributes of GT object
-----------------------

The attributes of the :py:class:`~gt.GT` class instance are listed here and are accessible via the python
``.`` operator i.e. ``<gt_obj>.<attribute>``.


.. list-table:: GT attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~gt.GT.name`
      - Name of the GT
    * - :py:data:`~gt.GT.type`
      - Serial object type. This is always equal to :py:data:`~aliases.GT_KEY`
    * - :py:data:`~gt.GT.handle`
      - Handle of the GT from cs_server
    * - :py:data:`~gt.GT.children`
      - Direct children of the GT
    * - :py:data:`~gt.GT.rx`
      - :py:class:`~ibert.rx.RX` child
    * - :py:data:`~gt.GT.tx`
      - :py:class:`~ibert.tx.TX` child
    * - :py:data:`~gt.GT.pll`
      - :py:class:`~ibert.pll.PLL` child
