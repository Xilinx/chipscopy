# ChipScoPy Release Notes

## 2024.2 - Release 

- 2024.2.1739397049 - February 12, 2024
- pin winpty only for windows, do not install on linux

- 2024.2.1733027508 - December 1, 2024
- Pin winpty version to continue Python 3.8 support for jupyter notebook
- Update README with 3.12 support

- 2024.2.1732283942 - November 22, 2024
- Fix chipscopy-examples directory not found with jupyter notebooks
      
- 2024.2.1732227392 - November 21, 2024
- Add US+ GTY IBERT example design and notebook
- Enhanced logging to handle additional logging domains
- Move example designs and jupyter notebooks out of pypi wheel to reduce file size
- Switch device program log to use hw_server service
- Add slr_index option to get_plm_log
- Add --force-reset option to device program
- Fix problems found in device program done and progress callbacks
- Add optional delay prior to create_session device scan to help initialization on slower systems
- Fix comparison case mismatch when jtag arch_name is missing from jtag node properties
- Upgrade required antlr dependency to 4.13.1 from 4.10
- Add missing YK Scan documentation
- Miscellaneous FAQ and documentation updates
- Host examples on github not pypi


## 2024.1 - June 12, 2024

- 2024.1.1717799899
- hw_server and cs_server compatibility updates
- Fixed device status register not updating after program
- Fixed duplicate field names in JTAG register
- Fixed examples not closing session
- Fixed some incorrect versions and links in examples
- Fixed procedure for computing bandwidth on PCs and ports in HBM
- Add link check before eye scan in cpm_decoupling example
- Improvements to documentation template


## 2024.1 - May 22, 2024

- 2024.1.dev1715183651
- Pre-release version for testing and verification

## 2023.2 - May 10, 2024

### Bugfix Release
- 2023.2.1715225694
- Versal HBM noc perfmon bugfix: corrected B/W computation for pseudo channels

## 2023.2 - Mar 18, 2024

### Bugfix Release

- 2023.2.1710645976
- Updated VHK158 design

## 2023.2 - Dec 8, 2023

### Bugfix Release

- 2023.2.1702018464
- Fixed jupyter notebook hangs on windows during eye scan plots by reverting Kaleido to previous version 0.1.0.post1
- We recommend using Python 3.8, 3.9, 3.10, or 3.11 with ChipScoPy


## 2023.2 - Oct 24, 2023

### Minor Release

- 2023.2.1698639225
- VHK158 Preliminary Support
  - HBM2E Evaluation Platform support with ChipScoPy
  - Known issue: DDR 2D Eye Scan is not working on this platform
- SysMon support for synchronous communication
- Enhanced device event tracking 
- Added support for decoupling CPM5 captive GTYP, associated example notebook included in release
  - Note: vpk120 only at this time

## 2023.1 - June 8, 2023

### Major Release

- 2023.1.1686244797
- NoC Perfmon features:
  - fixes for SSI devices and HBM
  - new basic noc perfmon example (other examples are now deprecated and will be removed in a future release)
- Device chain detection improvements
- Changed copyright from Xilinx to AMD
- Fixed missing docs on github for older 2021.2 release
- Clean up and overhaul of device scan algorithm to enable non-dpc communications (CR-1151331, CR-1151160)

## 2022.2 - December 5, 2022

### Minor Release

- 2022.2.1670292617
- ILA: Reorganized waveform functions export_waveform(), get_data(), get_probe_data()
- ILA: Advanced trigger state machine support
- Fixed device program progress callback
- IBERT: Handler for EYE_SCAN_ABORTED
- Switch csutil to argparse instead of click

## 2022.1 - June 9, 2022

###  Major release

- 2022.1.1654632407
- New VIO example
- Renamed chipscopy cli to "csutil"
- Updated 3rd party library dependency versions
- Enhanced Device class with new properties and error reporting 
- Better identification and handling of multiple devices in jtag chain
  - Both ARM DAP and Versal top-level target are now returned consistent with xsdb
  - Updated examples to match
  - To select a specific target use:
```
    # Typical case - one device on one board 
    device = session.devices.filter_by(family="versal").get()
```
- Allow delay for slower cables to identify jtag chains
- Fix error handling when deploying examples due to read-only file system
- More consistent to_json(), to_dict() methods for API classes
- Versal HBM2E core support
  - stack, memory controller cores
  - performance monitoring

## 2021.2 - December 11, 2021

### Minor release

- 2021.2.1639266951
- Compatibility with 2021.2 hw_server & cs_server versions
- ChipScoPy example design moving to a CED (https://github.com/Xilinx/XilinxCEDStore)
- Enum support for ILA Probes
- Added Jupyter notebook examples:
  - DDR 2D Eye Scan
  - NoC Performance Monitor
  

## 2021.1 - April 26, 2021

- 2021.1.1637713037

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
- PDI/LTX examples are included for the VCK190, VMK180, and VPK120 production boards - others can be built from CED sources.
- No Advanced ILA FSM trigger support in the ILA API.
- The code base is quickly evolving as we add features and address issues.
- Only Xilinx FPGA Devices are returned in the device list.

### Important Information

Using this API assumes you are comfortable scripting with Python 3, including downloading and setting up the Python interpreter, configuring virtual environments, and using pip for 3rd party package installation.

## License

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

**Additional Licenses**

TCF source files are licensed under terms of the Eclipse Public License 2.0. 
For additional details, see 

https://www.eclipse.org/legal/epl-2.0/
