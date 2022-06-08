# ChipScoPy Release Notes

## 2022.1 - June 9, 2022

###  Major release

- New VIO example
- Renamed chipscopy cli to "csutil"
- Updated 3rd party library dependency versions
- Enhanced Device class with new properties and error reporting 
- Better identification and handling multiple devices in jtag chain
- Allow delay for slower cables to identify jtag chains
- Fix error handling when deploying examples due to read-only file system
- More consistent to_json(), to_dict() methods for API classes
- Versal HBM2E core support
  - stack, memory controller cores
  - performance monitoring

## 2021.2 - December 11, 2021

### Minor release

- Compatibility with 2021.2 hw_server & cs_server versions
- ChipScoPy example design moving to a CED (https://github.com/Xilinx/XilinxCEDStore)
- Enum support for ILA Probes
- Added Jupyter notebook examples:
  - DDR 2D Eye Scan
  - NoC Performance Monitor
  

## 2021.1 - April 26, 2021

### What's New

Welcome to ChipScoPy! 

ChipScoPy is a Xilinx Python API to communicate with Xilinx devices and debug cores. It translates Python API calls into lower level TCF communication with the cs_server and hw_server applications.

### Python Features with Examples included in this release

- Versal Device Programming
- Versal Memory Access
- ILA (Integrated Logic Analyzer)
- VIO (Virtual IO)
- IBERT Link and Eye Scan
- DDR Memory Controller
- System Monitor
- NOC Performance Monitor

### Limitations and Known Issues
- ChipScoPy is not an interactive replacement for XSDB or Vivado Lab. It is a Python library.
- The ChipScoPy API version should match the hw_server and cs_server major/minor version.
- Only Xilinx Versal debug feature support is available in 2021.1. 
- PDI/LTX examples are included for the VCK190 and VMK180 production boards - others can be built from CED sources.
- No Advanced ILA FSM trigger support in the ILA API.
- The code base is quickly evolving as we add features and address issues.
- Only Xilinx FPGA Devices are returned in the device list.

### Important Information

Using this API assumes you are comfortable scripting with Python 3, including downloading and setting up the Python interpreter, configuring virtual environments, and using pip for 3rd party package installation.

## License

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

**Additional Licenses**

TCF source files are licensed under terms of the Eclipse Public License 2.0. 
For additional details, see 

https://www.eclipse.org/legal/epl-2.0/
