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

.. _gt_group:

GT Group
========

.. py:currentmodule:: chipscopy.api.ibert

GT Group object represent a collection of GT and PLL object(s)

Reset
-----

To reset all the ``RX``, ``TX`` and ``PLL`` in the GT Group, use the :py:meth:`~gt_group.GTGroup.reset` method

.. code-block:: python
    :emphasize-lines: 9

    # Get all IBERT cores in the device and select the first IBERT core for use
    iberts = device.ibert_cores
    ibert_0 = ibert.at(index=0)

    # Get all the GT Groups in the IBERT core
    all_gt_groups = ibert_0.gt_groups
    first_gt_group = all_gt_groups.at(index=0)

    first_gt_group.reset()

Attributes of GTGroup object
----------------------------

The attributes of the :py:class:`~gt_group.GTGroup` class instance are listed here and are accessible
via the python ``.`` operator i.e. ``<gt_group_obj>.<attribute>``.


.. list-table:: GTGroup attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~gt_group.GTGroup.name`
      - Name of the GT Group
    * - :py:data:`~gt_group.GTGroup.type`
      - Serial object type. This is always equal to :py:data:`~aliases.GT_GROUP_KEY`
    * - :py:data:`~gt_group.GTGroup.handle`
      - Handle of the GT Group from cs_server
    * - :py:data:`~gt_group.GTGroup.children`
      - Direct children of the GT Group
    * - :py:data:`~gt_group.GTGroup.gts`
      - Children of type :py:class:`~ibert.gt.GT`
    * - :py:data:`~gt_group.GTGroup.plls`
      - Children of type :py:class:`~ibert.pll.PLL`
