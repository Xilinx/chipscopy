# ChipScoPy FAQ

This document covers frequently asked questions about ChipScoPy.

- General information about ChipScoPy - [README.rst](README.rst)


**Q: What is ChipScoPy?**

**A:** ChipScoPy stands for the ChipScope Python API. This package provides a simple Python interface to program and debug features for Versal devices.


**Q: What is the minimum version of Vivado hw_server and cs_server required?**

**A:** Version 2020.3 for both the hw_server and cs_server is the minimum tool requirement.


**Q: What is the minimum Python version required to use ChipScoPy?**

**A:** Python 3.8 or above is required. To install Python, Go to python.org or the Microsoft Store and download Python 3.8 or better. 


**Q: How do I know which version of ChipScoPy to use with Vivado
cs_server and hw_server?**

**A:** The major and minor version of ChipScopy should always match the major and minor version of the Xilinx cs_server and hw_server tools. For instance, ChipScoPy 2021.1 will work against the 2021.1 cs_server and 2021.1 hw_server combination. ChipScoPy stores the matching tool information is stored in the variable `__vivado_version__`.

Using pip, you can specify install a specific version. `pip install chipscopy==2021.1` will install the latest 2021.1 version of ChipScoPy.


**Q: Does this API work for non-Versal devices?**

**A:** No. At this time, the ChipScoPy API only supports Versal devices and debug IP.

