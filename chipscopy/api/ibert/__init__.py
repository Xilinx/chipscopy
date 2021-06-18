# Copyright 2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from chipscopy.api.ibert.ibert import IBERT
from chipscopy.api.ibert.link.manager import LinkGroupManager, LinkManager
from chipscopy.api.ibert.eye_scan.manager import EyeScanManager
from chipscopy.api.ibert.yk_scan.manager import YKScanManager

# Aliases for ease of use
create_links = LinkManager.create_links
delete_links = LinkManager.delete_links
get_all_links = LinkManager.all_links

create_link_groups = LinkGroupManager.create_link_groups
delete_link_groups = LinkGroupManager.delete_link_groups
get_all_link_groups = LinkGroupManager.all_link_groups

create_eye_scans = EyeScanManager.create_eye_scans
delete_eye_scans = EyeScanManager.delete_eye_scans
get_all_eye_scans = EyeScanManager.all_eye_scans

create_yk_scans = YKScanManager.create_yk_scans
delete_yk_scans = YKScanManager.delete_yk_scans
get_all_yk_scans = YKScanManager.all_yk_scans
