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


ChipScoPy Quick Start
=====================

1. Install Python 3.8

   - Download from: `<https://www.python.org/downloads/>`_
   - Make sure to check "Add Python 3.8 to Path" when installing
   - Linux systems often use 'python3' instead of 'python' as the executable name. Use your python executable name for all python commands

2. Install ChipScoPy using the script below.

   - Windows Powershell:

   .. code-block::

      Invoke-WebRequest -Uri "https://github.com/Xilinx/chipscopy/raw/master/utils/get-chipscopy.py" -OutFile get-chipscopy.py; python get-chipscopy.py

   - Linux:

   .. code-block::

      curl -sSL https://github.com/Xilinx/chipscopy/raw/master/utils/get-chipscopy.py -o get-chipscopy.py; python3 get-chipscopy.py

3. The script terminates with instructions on how to activate the virtual environment.

   - You must activate the virtualenv subsequently, and every time the shell is re-launched.
   - Installation is complete.


If you encounter issues, or would like more detailed instructions, see the full :doc:`chipscopy_installation` instructions.
