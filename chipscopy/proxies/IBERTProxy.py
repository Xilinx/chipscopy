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

import typing
from typing import Any, Dict
from chipscopy.tcf import services
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy
from chipscopy.utils.logger import log

# NOTE: There should NOT be any dependency from proxy to server.
#  Instead define the service name locally in this file.
# from chipscope.server.harden.ibert.ibert_service import IBERTService

# NOTE: This name MUST match with the service name defined in the server side IBERT code
IBERT_SERVICE_NAME = "IBERT"

# NOTE: PLEASE USE THIS DOMAIN NAME IN ALL LOG MESSAGES FROM THIS FILE.
DOMAIN_NAME = "proxy_ibert"


class IBERTService(services.Service):
    def getName(self) -> str:
        return IBERT_SERVICE_NAME


class IBERTProxy(IBERTService):
    def __init__(self, channel):
        super(IBERTProxy, self).__init__(channel)
        self.listeners = {}

    def initialize(self, node_id: str, done) -> None:
        log[DOMAIN_NAME].debug("Sending initializeCmd")
        return self.send_xicom_command("initialize", (node_id,), done)

    def setup(self, options: Dict[str, Any], done):
        return self.send_xicom_command("setup", (options["node_id"], options), done)

    def get_layout(self, options: Dict[str, Any], done):
        return self.send_xicom_command("get_layout", (options["node_id"],), done)

    def read(self, options: Dict[str, Any], done):
        return self.send_xicom_command("read", (options["node_id"], options), done)

    def write(self, options: Dict[str, Any], done):
        return self.send_xicom_command("write", (options["node_id"], options), done)

    def get_property(self, options: Dict[str, Any], done):
        return self.send_xicom_command("get_property", (options["node_id"], options), done)

    def get_property_group(self, options: Dict[str, Any], done):
        return self.send_xicom_command("get_property_group", (options["node_id"], options), done)

    def set_property(self, options: Dict[str, Any], done):
        return self.send_xicom_command("set_property", (options["node_id"], options), done)

    def refresh_property(self, options: Dict[str, Any], done):
        return self.send_xicom_command("refresh_property", (options["node_id"], options), done)

    def refresh_property_group(self, options: Dict[str, Any], done):
        return self.send_xicom_command(
            "refresh_property_group", (options["node_id"], options), done
        )

    def commit_property(self, options: Dict[str, Any], done):
        return self.send_xicom_command("commit_property", (options["node_id"], options), done)

    def list_property_groups(self, options: Dict[str, Any], done):
        return self.send_xicom_command("list_property_groups", (options["node_id"],), done)

    def report_property(self, options: Dict[str, Any], done):
        return self.send_xicom_command("report_property", (options["node_id"], options), done)

    def add_to_property_watchlist(self, options: Dict[str, Any], done):
        return self.send_xicom_command(
            "add_to_property_watchlist", (options["node_id"], options), done
        )

    def remove_from_property_watchlist(self, options: Dict[str, Any], done):
        return self.send_xicom_command(
            "remove_from_property_watchlist", (options["node_id"], options), done
        )

    def start_eye_scan(self, options: Dict[str, Any], done):
        return self.send_xicom_command("start_eye_scan", (options["node_id"], options), done)

    def terminate_eye_scan(self, options: Dict[str, Any], done):
        return self.send_xicom_command("terminate_eye_scan", (options["node_id"], options), done)

    def get_eye_scan_parameters(self, options: Dict[str, Any], done):
        return self.send_xicom_command(
            "get_eye_scan_parameters", (options["node_id"], options), done
        )

    def start_yk_scan(self, options: Dict[str, Any], done):
        return self.send_xicom_command("start_yk_scan", (options["node_id"], options), done)

    def terminate_yk_scan(self, options: Dict[str, Any], done):
        return self.send_xicom_command("terminate_yk_scan", (options["node_id"], options), done)
