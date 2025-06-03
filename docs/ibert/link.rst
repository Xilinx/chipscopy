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

Link
====

.. py:currentmodule:: chipscopy.api.ibert

A link represents the physical connection between a TX and RX and can be used to modify the TX/RX parameters,
run 2D statistical eye scans and access other metrics for judging the quality of the link.


Create links
------------

Links can be created using :py:class:`~rx.RX` and :py:class:`~tx.TX`.
To create a link, use the factory function :py:func:`~create_links`.
Here's an example of creating a link

.. code-block:: python
    :emphasize-lines: 18, 21

    """
    Other imports
    """
    from chipscopy.api.ibert import create_links

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    quad_204 = one(ibert.gt_groups.filter_by(name="Quad_204"))

    ch_0 = one(quad_204.gts.filter_by(name="CH_0"))
    ch_1 = one(quad_204.gts.filter_by(name="CH_1"))
    ch_2 = one(quad_204.gts.filter_by(name="CH_2"))
    ch_3 = one(quad_204.gts.filter_by(name="CH_3"))

    # Create single link
    link_0 = one(create_links(rxs=ch_0.rx, txs=ch_0.tx))

    # Create multiple links in one shot
    remaining_3_links = create_links(rxs=[ch_1.rx, ch_2.rx, ch_3.rx], txs=[ch_1.tx, ch_2.tx, ch_3.tx])

.. note::
    When creating multiple links in one shot, please ensure that the length of the RX and TX lists are equal.


Since cs_server doesn't support all Xilinx GTs architectures OR non-Xilinx GTs, a link can be created with an
"Unknown" TX/RX.

.. note::
    Unknown TX/RX refers to TX/RXs that aren't supported by cs_server.

To do this, instead of TX/RX object, pass in an empty str i.e. ``""``. Example

.. code-block:: python

    # Create link with unknown TX
    link_0 = one(create_links(rxs=ch_0.rx, txs=""))

    # Create multiple links
    remaining_3_links = create_links(rxs=["", ch_2.rx, ch_3.rx], txs=[ch_1.tx, ch_2.tx, ""])

In the above snippet, ``link_0.tx = None``. Similarly, ``remaining_3_links[0].rx = None`` and
``remaining_3_links[2].tx = None``.


Attributes of Link object
-------------------------

The attributes of the :py:class:`~link.Link` class instance are listed here and are accessible via the python ``.``
operator i.e. ``<link_obj>.<attribute>``.


.. list-table:: Link attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~link.Link.name`
      - Name of the link
    * - :py:data:`~link.Link.handle`
      - Handle of the link
    * - :py:data:`~link.Link.rx`
      - :py:class:`~rx.RX` instance attached to the link
    * - :py:data:`~link.Link.tx`
      - :py:class:`~tx.TX` instance attached to the link
    * - :py:data:`~link.Link.link_group`
      - Link group the link is in
    * - :py:data:`~link.Link.eye_scan`
      - Eye scan object attached to the :py:data:`~link.rx`
    * - :py:data:`~link.Link.ber`
      - Bit Error Rate
    * - :py:data:`~link.Link.status`
      - Status of the link. If link is not locked, this is equal to ``"No Link"``
    * - :py:data:`~link.Link.line_rate`
      - Line rate with units
    * - :py:data:`~link.Link.bit_count`
      - #bits received
    * - :py:data:`~link.Link.error_count`
      - #errors received

Generate report
---------------

To generate a link report, call the :py:meth:`~link.Link.generate_report` method. This will
print the report in a tabular form to ``stdout``.

Example

.. code-block:: python

    link_0.generate_report()


.. image:: /ibert/images/link-report.png
    :width: 600
    :align: center


To get a string representation of the report, you can pass a callable to the function.


Get all links
-------------

To get all the links, use the function :py:func:`~get_all_links`.


Delete link
-----------

To delete a link, use the factory function :py:func:`~delete_links`.

.. code-block:: python
    :emphasize-lines: 15, 21

    """
    Other imports
    """
    from chipscopy.api.ibert import delete_links, get_all_links

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    # Assume 'link_0' is a Link object & 'remaining_3_links' is a list of Link's
    .
    .
    .
    # Delete one link
    delete_links(link_0)

    len(get_all_links())
    >>> 3

    # Delete 3 links
    delete_links(remaining_3_links)

    len(get_all_links())
    >>> 0

.. warning::
    Once the link is deleted, any references to the deleted link instance will be stale and are not safe to use.

Auto detect links
-----------------

To automatically detect links, use the factory function :py:func:`~detect_links`.

Links can be automatically detected using :py:class:`~session.Session` or :py:class:`~device.Devices` or :py:class:`~ibert.IBERT` or :py:class:`~gt_group.GTGroup` or :py:class:`~gt.GT` object(s) as target.

This API supports two optional callback functions to provide progress and done support.
The progress callback can be setup to check percentage complete and to get any new link created.
The done callback will be called at the end of auto link detection, this can be used to get list of all the links detected.

This API returns Future object if done or progress callback is provided otherwise a list of links detected is returned.

.. code-block:: python
    :emphasize-lines: 18, 21

    """
    Other imports
    """
    from chipscopy.dm.request import CsFuture
    from chipscopy.api.ibert import detect_links

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """
    def done_callback(f:CsFuture):
        result = f.result
        print(f"INFO: {result.info}")
        print(f"Progress : {result.progress}")
        links_created = result.new_link

    def progress_callback(f:CsFuture):
        result = f.result
        print(f"INFO: {result.info})
        print(f"Progress : {result.progress}")
        link_created = result.new_link


    # Detect links in a session and use callbacks (non-blocking)
    detect_future = detect_links(target=session, done=done_callback, progress=progress_callback)
    assert detect_future.error is None

    # Detect links in a session with no callbacks (blocking)
    links = detect_links(target=session)

.. note::
    The API ignores all :py:class:`~TX.tx` and :py:class:`~RX.rx` that are already part of a link.
