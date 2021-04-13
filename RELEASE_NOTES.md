# ChipScoPy Release Notes

## 2021.1 - March 14, 2021

### What's New

Welcome to ChipScoPy! 

ChipScoPy is a Xilinx Python API to communicate with Xilinx devices and debug cores. It translates Python API calls into lower level TCF communication with the cs_server and hw_server applications.

### Python Features with Examples included in this release

- Versal Device Programming
- Versal Memory Access
- ILA (Integrated Logic Analyzer)
- VIO (Virtual IO)
- DDR Memory Controller
- System Monitor
- NOC Performance Monitor

### Limitations and Known Issues
- The ChipScoPy version should match the hw_server and cs_server version
- hw_server and cs_server version must be 2021.1 or above
- Xilinx Versal Device Support Only in 2021.1
- Canned PDI/LTX examples are included for the VCK190 production board only 
- No Advanced ILA FSM trigger support
- This is not a complete replacement for Vivado Lab. A subset of features are supported.
- The code base is quickly evolving as we add features and address issues
- Only Xilinx Versal devices are currently supported and returned in the detected device chain

### Important Information

This API is an advanced hardware use case. Using this API assumes you are comfortable scripting with Python 3, including setting up virtual environments and pip for 3rd party package installation.

As the first beta release, a main goal is gathering user feedback. The API and implementation is likely to change as we collect feedback from active users.

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
