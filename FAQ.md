# ChipScoPy FAQ

This document covers frequently asked questions about ChipScoPy.

- General information about ChipScoPy - [README.md](README.md)

**Q: What is ChipScoPy?**

**A:** ChipScoPy stands for the ChipScope Python API. This package provides a simple Python interface to program and debug features for Xilinx Versal devices.

**Q: How do you pronounce ChipScoPy?**

**A:** chip-sco-pee and chip-sco-pie are both accepted. Sometimes it is entertaining to randomly flip during a conversation and see if others flip too.

**Q: What is the minimum version of Vivado hw_server and cs_server required?**

**A:** Version 2021.1 for both the hw_server and cs_server is the minimum tool requirement.

**Q: What is the minimum Python version required to use ChipScoPy?**

**A:** Python 3.8 or above is required. To install Python, Go to python.org or the Microsoft Store and download Python 3.8 or better. 

**Q: How do I know which version of ChipScoPy to use with Vivado cs_server and hw_server?**

**A:** The major and minor version of ChipScopy should always match the major and minor version of the Xilinx cs_server and hw_server tools. For instance, ChipScoPy 2021.1 will work against the 2021.1 cs_server and 2021.1 hw_server combination. ChipScoPy stores the matching tool information is stored in the variable `__vivado_version__`.

Using pip, you can specify install a specific version. `pip install chipscopy==2021.1` will install the latest 2021.1 version of ChipScoPy.

**Q: Does this API work for non-Versal devices?**

**A:** No. At this time, the ChipScoPy API only supports Versal devices and debug IP.

**Q: How can I print the ChipScoPy version?**

**A:** From an active ChipScoPy virtual environment:

```python
(venv) >python
Python 3.8.8 (tags/v3.8.8:024d805, Feb 19 2021, 13:18:16) [MSC v.1928 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import chipscopy
>>> print(chipscopy.__version__)
2021.1.1614310630
```

**Q: What does *"TCF channel terminated ConnectionRefusedError: [Errno 111] Connection refused"* mean ?**

**A:** This exception indicates a problem connecting to the hw_server or cs_server process.

- Make sure you have the version matched hw_server and cs_server running prior to using ChipScoPy.
- Check the hw_server and cs_server processes to ensure they did not unexpectedly terminate.
- Sometimes firewall services trap and prevent network communication to the servers. Turn off any firewall service and try to connect again.

**Q: What is the ChipScoPy source code copyright and license?**

**A:** Copyright 2021 Xilinx, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

*Additional Licenses*

TCF source files are licensed under terms of the Eclipse Public License 2.0. For additional details, see

https://www.eclipse.org/legal/epl-2.0/
