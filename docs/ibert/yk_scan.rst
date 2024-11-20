..
     Copyright (C) 2024, Advanced Micro Devices, Inc.
   
     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at
   
         http://www.apache.org/licenses/LICENSE-2.0
         
     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

YK Scan
========

.. py:currentmodule:: chipscopy.api.ibert

A YK scan helps us perform margin analysis on the channel over which the RX is receiving data.

Create YK scan
---------------

YK scans can be created using :py:class:`~rx.RX`.
To create an YK scan, use the factory function :py:func:`~create_yk_scans`.
Here's an example of creating YK scan for

* RX's

.. code-block:: python
    :emphasize-lines: 19, 24

    """
    Other imports
    """
    from more_itertools import one
    from chipscopy.api.ibert import create_yk_scans

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    quad_204 = one(ibert.gt_groups.filter_by(name="Quad_204"))

    ch_0 = one(quad_204.gts.filter_by(name="CH_0"))
    ch_1 = one(quad_204.gts.filter_by(name="CH_1"))
    ch_2 = one(quad_204.gts.filter_by(name="CH_2"))
    ch_3 = one(quad_204.gts.filter_by(name="CH_3"))

    # Creating YK scan for a single RX
    yk_scan_0 = one(create_yk_scans(target_objs=ch_0.rx))

    # OR

    # Creating YK scan for multiple RX's in one shot
    new_yk_scans = create_yk_scans(target_objs=[ch_1.rx, ch_2.rx, ch_3.rx])

Start YK scan
--------------

To start an YK scan, simply call the :py:meth:`~yk_scan.YKScan.start`.
.. code-block:: python

    yk_scan_0.start()

This will start the YK scan in a non-blocking fashion i.e. the call will return once the scan has started and
won't wait for completion of the scan. This allows you to continue doing other things while the YK scan is
in progress.

In order to get YK scan progress update, you can register a callback function with the
YK scan object before starting a scan. This can be done by setting the ``update_callback``attribute.

.. code-block:: python
    :emphasize-lines: 6

    def scan_progress_event_handler(progress_percent: float):
        pass # --> Add your logic here

    yk_scan_0.update_callback = scan_progress_event_handler

    yk_scan_0.start()

The progress callback should accept a single argument. 

.. note::
    The progress update callbacks is **not** called on the main thread.
    It is best to keep the logic in the event handlers as minimal as possible.


Accessing YK scan data
-----------------------

YK scan data can be accessed via the :py:data:`~yk_scan.YKScan.scan_data` attribute which is part of the :py:class:`~YK_scan.YKSample` class.

This instance stores the normalised slicer data from the MicroBlaze and the processed snr value. These are
accessible as shown.

.. list-table:: ScanData attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~YK_scan.ScanData.slicer`

    * - :py:data:`~YK_scan.ScanData.snr`
      - Access the SNR value being plotted.


Snippet below shows how to access the scan data given an instance of the :py:class:`~YK_scan.YKScan` class

.. code-block:: python
    :emphasize-lines: 4, 7

    # Assumed that we created "YK_scan_0" in a previous step and ran it to completion.

    # To access the raw slicer data
    YK_scan_0.scan_data.slicer

    # To access the snr value
    YK_scan_0.scan_data.snr

Stop YK scan
-------------

To stop an YK scan while it is in progress, call the :py:meth:`~YK_scan.YKScan.stop` method.

.. code-block:: python

    YK_scan_0.stop()

This will send the stop command to cs_server which will in-turn gracefully halt the YK scan test in the MicroBlaze.

If you would like to re-start a stopped scan, you can do so by calling the :py:meth:`~YK_scan.YKScan.start`
function again.

Get all YK scans
-----------------

To get all the links, use the function :py:func:`~get_all_yk_scans`.


Delete YK scan
---------------

To delete an YK scan, use the factory function :py:func:`~delete_yk_scans`.

.. code-block:: python
    :emphasize-lines: 11, 12

    """
    Other imports
    """
    from chipscopy.api.ibert import delete_yk_scans

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    # Assume we created 'yk_scan_0' through 'yk_scan_3'.
    delete_yk_scans(yk_scan_0)
    delete_yk_scans([yk_scan_1, yk_scan_2, yk_scan_3])

.. warning::
    Once the YK scan is deleted, any references to the deleted YK scan instance will be stale and are not safe to use.

