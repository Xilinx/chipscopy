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

TX
==

.. py:currentmodule:: chipscopy.api.ibert

A TX object is used to represent each transmitter in the GTs.

Reset
-----

To reset the ``TX``, use the :py:meth:`~tx.TX.reset` method

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

    first_gt.tx.reset()

Attributes of TX object
-----------------------

The attributes of the :py:class:`~tx.TX` class instance are listed here and are accessible via the python
``.`` operator i.e. ``<tx_obj>.<attribute>``.


.. list-table:: TX attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~tx.TX.name`
      - Name of the TX
    * - :py:data:`~tx.TX.type`
      - Serial object type. This is always equal to :py:data:`~aliases.RX_KEY`
    * - :py:data:`~tx.TX.handle`
      - Handle of the TX from cs_server
    * - :py:data:`~tx.TX.pll`
      - PLL driving this TX
    * - :py:data:`~tx.TX.link`
      - :py:class:`~link.Link` for the TX, if any
