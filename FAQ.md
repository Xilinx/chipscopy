# ChipScoPy FAQ

This document covers frequently asked questions about ChipScoPy.

- General information about ChipScoPy - [README.md](README.md)


---
**Q: What is ChipScoPy?**

**A:** ChipScoPy stands for the ChipScope Python API. This package provides a simple Python interface to program and debug features for Xilinx Versal devices.


---
**Q: How do you pronounce ChipScoPy?**

**A:** chip-sco-pee and chip-sco-pie are both accepted. Sometimes it is entertaining to randomly flip during a conversation and see if others flip too.


---
**Q: What is the minimum Python version required to use ChipScoPy?**

**A:** Python 3.8 or above is required. To install Python, Go to python.org or the Microsoft Store and download Python 3.8 or better. 


---
**Q: How do I know which version of ChipScoPy to use with Vivado cs_server and hw_server?**

**A:** For best results, ChipScopy should match the version of the Xilinx cs_server and hw_server tools. For instance, ChipScoPy 2022.1 will work best with the 2022.1 cs_server and 2022.1 hw_server combination. 

Using pip, you can specify install a specific version. `pip install chipscopy==2022.1.*` will install the 2022.1 version of ChipScoPy.

See the FAQ entry "Is there a policy regarding backward-compatibility in ChipScoPy?" for more details.


---
**Q: Is there a policy regarding backward-compatibility in ChipScoPy?**

**A:** Minor releases, for example within the same year (2022.1 and 2022.2) are expected to be backwards compatible with hw_server and cs_server of the same year. 

Different yearly releases (eg: 2022.2 and 2023.1) may have incompatibilities. 

It is fine to use ChipScoPy to program devices with PDIs created with older Vivado versions.


---
**Q: How can I print the ChipScoPy version?**

**A:** From an active ChipScoPy virtual environment:

ChipScoPy stores the matching tool information is stored in the variable `__vivado_version__`.

You may use the command line utility `csutil` installed with ChipScoPy.
```
csutil --version
```

Or use Python:

```python
(venv) >python
Python 3.8.8 (tags/v3.8.8:024d805, Feb 19 2021, 13:18:16) [MSC v.1928 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import chipscopy
>>> print(chipscopy.__version__)
2021.1.1614310630
```

---
**Q: Does this API work for non-Versal devices?**

**A:** No. At this time, the ChipScoPy API only supports Versal devices and debug IP.

---
**Q: What does *"TCF channel terminated ConnectionRefusedError: [Errno 111] Connection refused"* mean ?**

**A:** This exception indicates a problem connecting to the hw_server or cs_server process.

- Make sure you have the version matched hw_server and cs_server running prior to using ChipScoPy.
- Check the hw_server and cs_server processes to ensure they did not unexpectedly terminate.
- Sometimes firewall services trap and prevent network communication to the servers. Turn off any firewall service and try to connect again.

---
**Q: How do I fix the error *"Activate.PS1 cannot be loaded because running scripts is disabled on this system..."* ?**

Windows Powershell disables script running by default for security. You can relax the default execution policy in PowerShell, or use cmd.exe instead of PowerShell.

For more details about using Set-ExecutionPolicy to relax script blocking in PowerShell, see Microsoft's PowerShell documentation page:

https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies

---
**Q: What is the ChipScoPy source code copyright and license?**

**A:** 
Copyright (C) 2021-2022, Xilinx, Inc.

Copyright (C) 2022-2023, Advanced Micro Devices, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

*Additional Licenses*

TCF source files are licensed under terms of the Eclipse Public License 2.0. For additional details, see

https://www.eclipse.org/legal/epl-2.0/

---
**Q: Displaying eye scan images on Windows hangs in jupyter notebooks. What causes this issue, and how can I fix it?**

**A:** There is a [bug](https://github.com/plotly/Kaleido/issues/150) with some versions of the 3rd party Kaleido library that causes static image export to hang.

By default, `pip install chipscopy[core-addons]` will install a working kaleido version.

To manually fix this, make sure your kaleido version is 0.1.0.post1 on windows.

`pip install kaleido==0.1.0.post1`

Note: This is a windows fix only and does not apply to Linux.


---
**Q: Why do I get the following error when installing ChipScoPy[core-addons]:**

    error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools"


**A:**
The 3rd party Pandas 1.5 library is not pre-built for Python 3.12. Installing Pandas requires C++ build tools to be installed on Windows.

Option 1: Use a Python interpreter less than 3.12. Versions 3.8 through 3.11 have pre-built wheels available.

Option 2: Install Microsoft Build Tools as described in the error message. This is a free download from Microsoft from:

http://visualstudio.microsoft.com/visual-cpp-build-tools/

---
