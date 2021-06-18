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

import sys
import copy
from typing import List, Union, ClassVar
import logging
from pathlib import Path
from logging import handlers

import loguru


class ParodyLogger:
    def trace(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def success(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def critical(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        return self

    def __getitem__(self, item):
        return self


class CSSLogger:
    # Default format
    default_format: ClassVar[str] = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<m>{extra[domain]: >20}</m> | "
        "<cyan>{name: >50}</cyan> | "
        "<cyan>{line: <4}</cyan> | "
        "<level>{message}</level>"
    )

    def __init__(self):
        self._parody_logger = ParodyLogger()

        loguru.logger.remove()

        self.logger: loguru.Logger = copy.deepcopy(loguru.logger)
        # Enable all modules, we'll enforce domain using record filter
        self.logger.enable("")

        self.logger_for_domain = dict()

        self.domain_enabled = dict()

        self.default_sink_id: int = None

        self.current_log_level: loguru.Level = None

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            return
        msg = args[0]
        log["client"].info(msg)

    def __getattr__(self, item) -> loguru.logger:
        if not self.domain_enabled.get(item, False):
            return self._parody_logger
        return self._get_logger_for_domain(item)

    def __getitem__(self, item) -> loguru.logger:
        if not self.domain_enabled.get(item, False):
            return self._parody_logger
        return self._get_logger_for_domain(item)

    def _send_record_to_sink(self, record) -> bool:
        return self.domain_enabled.get(record["extra"]["domain"], False)

    def _get_logger_for_domain(self, domain):
        if domain not in self.logger_for_domain:
            new_logger = self.logger.bind(domain=domain)
            self.logger_for_domain[domain] = new_logger
            if domain not in self.domain_enabled:
                # Disable domain logging by default.
                self.domain_enabled[domain] = False

        return self.logger_for_domain[domain]

    def is_domain_enabled(self, domain: str, level: str) -> bool:
        level_info = self.logger.level(level)
        return self.domain_enabled.get(domain, False) and level_info.no >= self.current_log_level.no

    def enable_domain(self, domain_name: Union[str, List[str]]):
        if isinstance(domain_name, str):
            domain_name = [domain_name]

        for domain in domain_name:
            # Need not check if domain is in domain_logging_status.
            # This is in case the user enables the domain before logging any message.
            self.domain_enabled[domain] = True

    def disable_domain(self, domain_name: Union[str, List[str]]):
        if isinstance(domain_name, str):
            domain_name = [domain_name]

        for domain in domain_name:
            if domain in self.domain_enabled:
                self.domain_enabled[domain] = False

    def change_log_level(self, level: str):
        level_info = self.logger.level(level)

        if self.default_sink_id is not None:
            # Delete only the stdout sink. Don't touch any others that might have been added by user
            self.logger.remove(self.default_sink_id)

        self.default_sink_id = self.logger.add(
            sink=sys.stdout,
            level=level,
            format=CSSLogger.default_format,
            filter=self._send_record_to_sink,
        )

        self.current_log_level = level_info

    def add_file_handler(self, full_path: Union[str, Path], level_name: str) -> int:
        level_info = self.logger.level(level_name)
        return self.logger.add(full_path, format=CSSLogger.default_format, level=level_info.name)

    def add_queue_handler(self, queue, level_name: str) -> int:
        queue_handler = logging.handlers.QueueHandler(queue)
        level_info = self.logger.level(level_name)
        return self.logger.add(
            queue_handler, format=CSSLogger.default_format, level=level_info.name
        )


# NOTE - Server side code should not import this! Only client side code should use this.
#  Server side code should import from init in server
log = CSSLogger()
