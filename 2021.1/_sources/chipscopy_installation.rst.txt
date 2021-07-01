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

ChipScoPy requires an installed Python. There are several ways to configure your system with Python. We recommend and document a no-frills `Basic Python Installation`_.

If you're a seasoned python user, you can skip ahead to `Manual Installation`_. This assumes you have python installed and know how to manage environments, packages, and pip configuration.


Basic Python Installation
-------------------------

This section covers installing the Python base interpreter. Two options for obtaining a suitable Python are noted in this section. The first, `Vivado Distributed Python`_, describes how to use the Python bundled with Vivado. The alternate section, `Dedicated Python`_, is for non Vivado users or users who want a different version of Python installed for use with ChipScoPy. A single version of Python will execute ChipScoPy--ergo, do not install multiple Pythons via different methods.


Vivado Distributed Python
^^^^^^^^^^^^^^^^^^^^^^^^^

Beginning in 2021.1, the unified Vivado installer will deliver a suitable Python during the install operation. This Python is located at the following operating system-dependent locations:

* Linux

    .. code-block::

       /path_to_xilinx_tools/Vivado/<vivado_version>/tps/lnx64/python-<python_version>
       e.g.:
       /opt/xilinx/Vivado/2021.1/tps/lnx64/python-3.8.3

    To use this Python, set your path and loader path by (bash syntax):

    .. code-block::

       export PATH=$PATH:/opt/xilinx/Vivado/2021.1/tps/lnx64/python-3.8.3/bin
       export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/xilinx/Vivado/2021.1/tps/lnx64/python-3.8.3/lib

* Windows

    .. code-block::

       <drive_spec>:\path_to_xilinx_tools\Vivado\<vivado_version>\tps\win64\python-<python_version>
       e.g.:
       C:\Xilinx\Vivado\2021.1\tps\win64\python-3.8.3

    To use this Python, amend this to your user or system-wide %PATH% environment variable

    .. code-block::

       C:\Xilinx\Vivado\2021.1\tps\win64\python-3.8.3\bin


Dedicated Python
^^^^^^^^^^^^^^^^

To install a dedicated Python, one that was not shipped as part of Vivado, navigate to:
`<https://www.python.org/downloads/>`_. ChipScoPy requires Python 3.8 or newer.

Windows 10 (v1909) users can install python through the Microsoft Store by searching for Python and selecting the language version you want to install. At this time, Python 3.8 offers the most stability and usability. Python 3.9 has not been tested with ChipScoPy.

Download and install Python. When it asks if you want to update the ``PATH`` variable, it's highly recommended you
take that action. Once you have Python installed, you may use the setup script in
`Automated Installer`_ to complete the rest of the installation.

.. warning:: **NEVER** invoke ``sudo`` to install Python packages. Installing Python packages with ``sudo`` can
             accidentally overwrite existing system files.


Virtual Environments 
--------------------

A virtual environment is an isolated Python environment. It allows ChipScoPy and its dependencies to be installed
without interfering with the behavior of any other Python applications. The use of virtual environments is best
practice.

.. note:: For more information about Python virtual environments, check out the official
          `Python Virtual Environment Documentation <https://docs.python.org/3.7/tutorial/venv.html>`_.


Automated Installer
-------------------

An installation script is provided to simplify the installation of ChipScoPy in a Python virtual environment.

1. Copy and paste the snippet below into the Powershell window, if running Windows; or into your terminal if running Linux.

    This will set up a virtual environment, install ChipScoPy, and dependencies. Then it will unpack the examples delivered with ChipScoPy, optionally start jupyter notebook server, and ask the user if they want a shortcut installed on the desktop for future sessions.

    * Windows:

        .. code-block:: powershell

            Invoke-WebRequest -Uri "https://github.com/Xilinx/chipscopy/raw/master/utils/get-chipscopy.py" -OutFile get-chipscopy.py; python get-chipscopy.py

    * Linux:

        .. code-block:: shell

            curl -sSL https://github.com/Xilinx/chipscopy/raw/master/utils/get-chipscopy.py -o get-chipscopy.py; python3 get-chipscopy.py


2. Follow the interactive script prompts. It will ask where the virtual environment should be created. After the environment is created, pip will proceed with the installation of chipscopy.

.. note:: These scripts will install the latest version of the ChipScoPy package. To install alternate versions of the package see the alternate invocation in `Install ChipScoPy`_.

3. The final step in the installer is to unpack the examples. Pay attention to the script output as extraction will fail if the examples are already unpacked in the target location.

The script terminates with instructions on how to activate the virtual environment. You must activate the
virtualenv subsequently, and every time the shell is re-launched.

Installation is complete. The rest of this document outlines the manual installation process. It is not necessary to
perform these steps when the installer script is used.

The next step is to explore the examples.


-------------------


Manual Installation
-------------------

This section is for advanced Python users. It describes the manual steps to setup the environment. If anything here is unfamiliar, or there are issues, feel free to use the installer described in `Automated Installer`_.


Install ChipScoPy
^^^^^^^^^^^^^^^^^

If you used one of the installer scripts above, this section was already done by the installer script. Skip ahead to the section `Setup Dependencies`_.

It's time to install the ChipScoPy package itself.

* To install the latest version of ChipScoPy into the active Python virtual environment:

    .. code-block:: shell

        (chipscopy) > python -m pip install chipscopy

* To install a specific version of ChipScoPy into the active Python virtual environment:

    .. code-block:: shell

        (chipscopy) > python -m pip install chipscopy==2021.1.*


Setup Dependencies
^^^^^^^^^^^^^^^^^^

With the environment active you may need to install some additional packages that aren't listed in the ChipScoPy project-level dependencies. If you intend to use any of these client examples, then you'll need to get additional items.

.. code-block:: none

    python -m pip install chipscopy[jupyter]
    python -m pip install chipscopy[core-addons]


Be sure your virtual environment is active before installing these additional dependencies.


Congratulations -- if you're still awake and you've followed the steps till here, you are the proud owner of a functional Python setup. The next step is to start exploring the examples.


Install ChipScoPy Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that the ChipScoPy package has been installed, there is an alias to install the examples into a particular directory
chosen by the user.

.. code-block:: shell

    (chipscopy) > chipscopy-get-examples
    The following examples  will be delivered to `/home/user/chipscopy-examples`:
    - ddr_example.ipynb
    - ddr_example.py
    - basic_detect.py
    ...


Note where these files are extracted.


Starting Jupyter
^^^^^^^^^^^^^^^^^^^^^

Assuming you installed the ``jupyter`` package into your virtual environment, you can use the notebooks provided with
the examples.

Launch the server:

.. code-block:: shell

    (chipscopy) > jupyter notebook


This should launch the server in a browser window on your local machine. Simply navigate to the directory to which you
deployed the ChipScoPy examples and then you may run any notebook included with the release.


ChipScoPy Updates
^^^^^^^^^^^^^^^^^

As the development team pushes fixes and features; ``pip``, again, is the recommended tool for grabbing the latest software.

.. code-block:: shell

    (chipscopy) > python -m pip install --upgrade chipscopy


To get the latest software for a specific release (2021.1 in this example):

.. code-block:: shell

    (chipscopy) > python -m pip install --upgrade chipscopy==2021.1.*


And don't forget to extract the latest examples after each package update:

.. code-block:: shell

    (chipscopy) > chipscopy-get-examples
