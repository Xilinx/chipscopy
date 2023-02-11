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

.. _chipscopy_installation:

ChipScoPy Installation
======================

ChipScoPy requires Python 3.8 or greater. There are several ways to configure your system to use the ChipScoPy API. This page will cover the following step-by-step installation procedure.

    - `Step 1: Python Installation`_
    - `Step 2: Set up Virtual Environment`_
    - `Step 3: Install ChipScoPy`_
    - `Step 4: Install Dependencies`_
    - `Step 5: Install Examples`_
    - `Step 6: Open Jupyter Notebook`_
    - `Step 7: Update ChipScoPy`_
    - `Step 8: Update ChipScoPy Examples`_


Step 1: Python Installation
---------------------------

This section covers installing the Python base interpreter. Two options for obtaining a suitable Python are noted in this section. 

- `Option 1 - Install Python from python.org`_ is for users who are able to download and install the official Python. This is the recommended approach.

- `Option 2 - Vivado Distributed Python`_ describes how to use the Python bundled with Vivado. 

A single version of Python will execute ChipScoPy--ergo, do not install multiple Pythons via different methods.

.. warning:: **NEVER** invoke ``sudo`` to install Python packages. Installing Python packages with ``sudo`` can accidentally overwrite existing system files.

Option 1 - Install Python from python.org
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the recommended installation procedure to get the latest available Python interpreter from Python.org.

To install Python, navigate to:
`<https://www.python.org/downloads/>`_. Locate and install the latest Python 3.8 or newer for your operating system.

.. note:: Make sure to check the box to add Python to the PATH during installation.


Option 2 - Vivado Distributed Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Beginning in 2021.1, the unified Vivado installer will deliver a suitable Python during the install operation. This Python is located at the following operating system-dependent locations:

**Linux:**

.. code-block:: shell

   /path_to_xilinx_tools/Vivado/<ver>/tps/lnx64/python-<ver>
   e.g.:
   /opt/xilinx/Vivado/2021.2/tps/lnx64/python-3.8.3

   To use this Python, set your path and loader path by (bash syntax):
   export PATH=$PATH:/opt/xilinx/Vivado/2021.2/tps/lnx64/python-3.8.3/bin
   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/xilinx/Vivado/2021.2/tps/lnx64/python-3.8.3/lib


**Windows**

.. code-block:: shell

   <drive_spec>:\path_to_xilinx_tools\Vivado\<ver>\tps\win64\python-<ver>
   e.g.:
   C:\Xilinx\Vivado\2021.2\tps\win64\python-3.8.3

   To use this Python, amend this to your user or system-wide %PATH% environment variable
   C:\Xilinx\Vivado\2021.2\tps\win64\python-3.8.3\bin


Step 2: Set up Virtual Environment
----------------------------------

A virtual environment is an isolated Python environment. It allows ChipScoPy and its dependencies to be installed without interfering with the behavior of any other Python applications. The use of virtual environments is best practice.

For more information about Python virtual environments, check out the official
`Python Virtual Environment Documentation <https://docs.python.org/3.8/tutorial/venv.html>`_.

.. note:: Linux systems often name the python command 'python3' instead of 'python'. In that case, substitute 'python3' as needed in the commands below.
          

2.1: Install Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following will create a virtual environment sandbox and install python into the virtual environment. 

Installation assumes you are using bash on linux, or the PowerShell on Windows. The Windows PowerShell can be accessed by right clicking on the start menu and selecting "Windows PowerShell".


.. code-block:: shell

    > python -m venv venv


2.2: Activate Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Activate the virtual environment. The location of the activate script is different depending on operating system. You will need to re-activate the virtual environment whenever you reopen a fresh bash or PowerShell terminal.

**Linux:**

.. code-block:: shell

    > source venv/bin/activate

**Windows:**

.. code-block:: shell

    > venv/Scripts/activate

.. note:: Make sure to always activate the Python virtual environment before you use ChipScoPy.


Step 3: Install ChipScoPy
-------------------------

It's time to install the ChipScoPy package itself. With your Python environment active run:

.. code-block:: shell

    # installs latest version 
    (venv) > python -m pip install chipscopy


If you want to install a specific version, run:


**Linux:**

.. code-block:: shell

    # installs 2021.2 version of chipscopy
    (venv) > python -m pip install 'chipscopy==2021.2.*'

**Windows:**

.. code-block:: shell

    # installs 2021.2 version of chipscopy
    (venv) > python -m pip install chipscopy==2021.2.*


Step 4: Install Dependencies
----------------------------

With the virtual environment active you may want to install some additional packages that aren't listed in the ChipScoPy project-level dependencies. If you intend to use any of these client examples, then you’ll need to get additional packages.

Run the following commands to install the additional support packages:

.. code-block:: shell

    (venv) > python -m pip install chipscopy[core-addons]
    (venv) > python -m pip install chipscopy[jupyter]


Congrats--if you're still awake and you've followed the steps till here, you are the proud owner of a functional Python setup. Next steps are to start exploring the examples.


Step 5: Install Examples
------------------------

Now that the ChipScoPy package has been installed, there is a script to install the examples into a particular directory chosen by the user.

.. code-block:: shell

    (venv) > chipscopy-get-examples

    The following examples  will be delivered to `/home/user/chipscopy-examples`:
    - ddr_example.ipynb
    - ddr_example.py
    - basic_detect.py
    ...


Make note of the location to which these are extracted. This location contains example python code and example designs.


Step 6: Open Jupyter Notebook
-----------------------------

Assuming you installed the ``jupyter`` package into your virtual environment, you can use the jupyter notebooks provided with the examples. 

Launch the jupyter notebook server:

.. code-block:: shell

    (venv) > jupyter notebook


This should launch the server in a browser window on your local machine. Follow the link sent to the console, and then navigate to the directory to which you deployed the ChipScoPy examples. Notebook example files have the '.ipynb' extension.

.. note:: The examples assume you have a hw_server and cs_server running on the local machine connected to the board.

Make sure to start the hw_server and cs_server applications in separate terminal windows on the board's host, and note the URL connection info for each, if not the localhost.  You will need this URL info for the respective example Jupyter notebooks).

Start the hardware server:

.. code-block:: shell

    hw_server

Start the chipscope server:

.. code-block:: shell

    cs_server


The hw_server and cs_server applications are included in Vivado and
Vivado Lab Edition. They can be downloaded from
https://www.xilinx.com/support/download.html


Step 7: Update ChipScoPy
------------------------

As the development team pushes fixes and features; ``pip``, again, is the recommended tool for grabbing the latest software.

To get the latest software release:

.. code-block:: shell

    (venv) > python -m pip install --upgrade chipscopy


To get the latest numbered software release (2021.2 in this example):

**Linux**

.. code-block:: shell

    (venv) > python -m pip install --upgrade 'chipscopy==2021.2.*'

**Windows**

.. code-block:: shell

    (venv) > python -m pip install --upgrade chipscopy==2021.2.*


Step 8: Update ChipScoPy Examples
---------------------------------

ChipScoPy examples are updated frequently. To extract the latest examples after each ChipScoPy update, run this command again:

.. code-block:: shell

    (venv) > chipscopy-get-examples
