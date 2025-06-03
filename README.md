# 🐍 ChipScoPy README

[![](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![](https://raw.githubusercontent.com/Xilinx/chipscopy/master/docs/images/chipscopy_logo_head_right_transparent_background.png)

ChipScoPy is an open-source project from AMD that enables high-level control of debug IP running in Versal hardware. 
Using a simple Python API, developers can control and communicate with ChipScope® debug IP such as the Integrated Logic Analyzer (ILA), Virtual IO (VIO), IBERT, device memory, and more.
ChipScoPy was created for Versal devices but contains some limited support for Ultrascale+ devices (see Limitations below).

---

![](https://raw.githubusercontent.com/Xilinx/chipscopy/master/docs/images/chipscopy_overview.png)

---

## Limitations

- ChipScoPy does not work with older devices such as 7-Series devices.
- ChipScoPy only supports IBERT GTY in Ultrascale+ devices, not other debug features like ILA or VIO.

## Python Version Support

Python versions 3.9, 3.10, 3.11, 3.12, or 3.13 will work with ChipScoPy.

## Quick Links

[ChipScoPy Overview](https://xilinx.github.io/chipscopy/2024.2/overview.html)

[System Requirements](https://xilinx.github.io/chipscopy/2024.2/system_requirements.html)

[ChipScoPy Installation](https://xilinx.github.io/chipscopy/2024.2/chipscopy_installation.html)

[ChipScoPy Examples](https://github.com/Xilinx/chipscopy/tree/master/chipscopy/examples)

[FAQ](https://github.com/Xilinx/chipscopy/blob/master/FAQ.md)

[API Documentation](https://xilinx.github.io/chipscopy/)

## **ChipScoPy Installation PyPI Package Dependencies**

During ChipScoPy installation, the following packages (and any dependencies) are installed from the Python Package Index (PyPI) using pip.

| Package                                                                    | License    |
|:-------------------------------------------------------------------------- |:----------:|
| [Requests](https://pypi.org/project/requests/)                             | Apache-2.0 |
| [more-itertools](https://pypi.org/project/more-itertools/)                 | MIT        |
| [typing_extensions](https://pypi.org/project/typing-extensions/)           | PSF        |
| [loguru](https://pypi.org/project/loguru/)                                 | MIT        |
| [importlib_metadata](https://pypi.org/project/importlib-metadata/)         | Apache-2.0 |
| [rich](https://pypi.org/project/rich/)                                     | MIT        |
| [Click](https://pypi.org/project/click/)                                   | BSD        |
| [antlr4-python3-runtime](https://pypi.org/project/antlr4-python3-runtime/) | BSD        |
| [kaleido](https://pypi.org/project/kaleido/)                               | MIT        |
| [plotly](https://pypi.org/project/plotly/)                                 | MIT        |
| [notebook](https://pypi.org/project/notebook/)                             | BSD        |
| [ipywidgets](https://pypi.org/project/ipywidgets/)                         | BSD        |
| [pandas](https://pypi.org/project/pandas/)                                 | BSD        |
| [matplotlib](https://pypi.org/project/matplotlib/)                         | PSF        |
| [PyQt5](https://pypi.org/project/PyQt5/)                                   | GPL        |
| [ipympl](https://pypi.org/project/ipympl/)                                 | BSD        |

# 

Copyright (C) 2021-2022, Xilinx, Inc.

Copyright (C) 2022-2025, Advanced Micro Devices, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
