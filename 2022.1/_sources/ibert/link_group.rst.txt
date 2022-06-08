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

Link Group
==========

.. py:currentmodule:: chipscopy.api.ibert

A link group object holds a set of link objects. This container makes it easy to group and interact with multiple links at the same time.


Create link group
-----------------

To create a link group, use the factory function :py:func:`~create_link_groups`.
Here's an example of creating a link group

.. code-block:: python
    :emphasize-lines: 11, 14

    """
    Other imports
    """
    from chipscopy.api.ibert import create_links, create_link_groups

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    # Create a single link group
    link_group_0 = create_link_groups(descriptions="This is a test link group")

    # Create multiple link groups in one shot
    three_link_groups create_link_group(descriptions=["Group 1", "Group 3", "Group 3"])

Attributes of LinkGroup object
------------------------------

The attributes of the :py:class:`~link.group.LinkGroup` class instance are listed here and are accessible
via the python ``.`` operator i.e. ``<link_group_obj>.<attribute>``.


.. list-table:: LinkGroup attributes
    :widths: 25 50
    :header-rows: 1

    * - Attribute
      - Description
    * - :py:data:`~link.group.LinkGroup.name`
      - Name of the link group
    * - :py:data:`~link.group.LinkGroup.description`
      - Description of the link group
    * - :py:data:`~link.group.LinkGroup.links`
      - All :py:class:`~link.Link` objects in the link group


Add link
--------

To add link(s) to the link group use the :py:meth:`~link.group.LinkGroup.add` method.

.. code-block:: python
    :emphasize-lines: 16, 21, 24

    """
    Other imports
    """
    from chipscopy.api.ibert import create_links, create_link_groups

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    # Create single link
    link_0 = one(create_links(rxs=ch_0.rx, txs=ch_0.tx))

    # Create multiple links in one shot
    remaining_3_links = create_links(rxs=[ch_1.rx, ch_2.rx, ch_3.rx], txs=[ch_1.tx, ch_2.tx, ch_3.tx])

    # Assume we created 'link_group_0'
    .
    .
    .
    # Add single link
    link_group_0.add(link_0)

    # Add multiple links
    link_group_0.add(remaining_3_links)

    len(link_group_0.links)
    >>> 4


Remove link
-----------

To remove link(s) from the link group use the :py:meth:`~link.group.LinkGroup.remove` method.

.. code-block:: python
    :emphasize-lines: 9, 12

    # Assume we created 'link_group_0', added 'link_0' and 'remaining_3_links' to it
    .
    .
    .
    len(link_group_0.links)
    >>> 4

    # Remove single link
    link_group_0.remove(link_0)

    # Remove multiple links
    link_group_0.remove(remaining_3_links)

    len(link_group_0.links)
    >>> 0


Get all link groups
-------------------

To get all the link groups, use the function :py:func:`~get_all_link_groups`.


Delete link group
-----------------

To delete a link, use the factory function :py:func:`~delete_link_groups`.

.. code-block:: python
    :emphasize-lines: 14, 23

    """
    Other imports
    """
    from chipscopy.api.ibert import delete_link_groups, get_all_links, get_all_link_groups

    """
    Boilerplate stuff - Create a session, get the IBERT core etc etc
    """

    # Assume we created 'link_group_0' and added 'link_0'
    # Also assume that we created 'link_group_1' and added 'remaining_3_links' to it

    # This will delete only the link group and not the links
    delete_link_groups(link_group_0)

    len(get_all_links())
    >>> 4

    len(get_all_link_groups())
    >>> 1

    # This will delete the link group + the links in it
    delete_link_groups(link_group_1, delete_links_in_group=True)

    len(get_all_links())
    >>> 1

    len(get_all_link_groups())
    >>> 0

.. warning::
    Once the link group is deleted, any references to the deleted link group instance will be stale and unsafe to use.

