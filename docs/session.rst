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

Session
=======


Factory methods
---------------

Session creation/deletion **should** always be done using factory methods.

- For creation use :py:meth:`~chipscopy.create_session`

.. code-block:: python
    :emphasize-lines: 6

    from chipscopy import create_session

    CS_URL = "TCP:localhost:3042"
    HW_URL = "TCP:localhost:3121"

    session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)

- For deletion use :py:meth:`~chipscopy.delete_session`

.. code-block:: python
    :emphasize-lines: 3

    from chipscopy import delete_session

    delete_session(session)


Alternatively, context managers like ``with`` can be used to auto manage session lifecycle as shown in below example

.. code-block:: python
    :emphasize-lines: 6

    from chipscopy import create_session

    CS_URL = "TCP:localhost:3042"
    HW_URL = "TCP:localhost:3121"

    with create_session(cs_server_url=CS_URL, hw_server_url=HW_URL) as session:
        # Your business logic here
        device = session.devices.at(0)

    # 'session' is automatically deleted after the with block gets done
    print()


Reference
---------

.. toctree::
   :maxdepth: 1

   /session/references.rst