# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
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
import logging
from typing import List, Optional, Union
from pathlib import Path
from logging import handlers


class DomainFilter(logging.Filter):
    """Filter that checks whether a domain is enabled on the owning CSSLogger."""

    def __init__(self, css_logger: "CSSLogger"):
        super().__init__()
        self._css_logger = css_logger

    def filter(self, record: logging.LogRecord) -> bool:
        domain = getattr(record, "domain", None)
        if domain is None:
            return True
        return self._css_logger.domain_enabled.get(domain, False)


class CSSFormatter(logging.Formatter):
    """Formatter that includes the domain field."""

    DEFAULT_FORMAT = (
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(domain)20s | "
        "%(name)50s | %(lineno)-4d | %(message)s"
    )
    DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "domain"):
            record.domain = "unknown"
        return super().format(record)


class DomainLogger:
    """Thin wrapper that injects domain context into every log record."""

    def __init__(self, stdlib_logger: logging.Logger, domain: str):
        self._logger = stdlib_logger
        self._domain = domain

    def _log(self, level: int, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 3)
        if self._logger.isEnabledFor(level):
            extra = dict(kwargs.pop("extra", None) or {})
            extra["domain"] = self._domain
            kwargs["extra"] = extra
            self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)


class CSSLogger:
    """Domain-based logging manager backed by stdlib logging.

    Each domain maps to a DomainLogger.  Handlers are attached to a single
    root ``logging.Logger`` instance; domain filtering is done via
    ``DomainFilter`` on each handler.
    """

    _instance_counter: int = 0

    def __init__(self, logger_name: str = "chipscopy"):
        # Use a unique internal logger name to avoid interfering with
        # application-level logging configuration on the same name.
        CSSLogger._instance_counter += 1
        internal_name = f"_css.{logger_name}.{CSSLogger._instance_counter}"
        self._logger = logging.getLogger(internal_name)
        self._logger.setLevel(logging.DEBUG)  # allow all; handlers do filtering
        self._logger.propagate = False

        self.logger_for_domain: dict = {}
        self.domain_enabled: dict = {}

        self._domain_filter = DomainFilter(self)

        self._default_handler: Optional[logging.Handler] = None
        self._handlers: dict = {}  # id(handler) -> handler
        self._next_handler_id: int = 1

        self.current_log_level: Optional[str] = None

    # ------------------------------------------------------------------
    # Domain management
    # ------------------------------------------------------------------

    def get_logger(self, domain: str) -> DomainLogger:
        """Return a logger for *domain*, auto-registering if needed.

        Always returns the same DomainLogger instance for a given domain.
        Filtering of disabled domains is handled by DomainFilter on each
        handler, so enabling/disabling a domain takes effect immediately
        regardless of when get_logger was called.
        """
        if domain not in self.logger_for_domain:
            domain_logger = DomainLogger(self._logger, domain)
            self.logger_for_domain[domain] = domain_logger
            if domain not in self.domain_enabled:
                self.domain_enabled[domain] = False
        return self.logger_for_domain[domain]

    def is_domain_enabled(self, domain: str, level: str) -> bool:
        level_no = getattr(logging, level.upper(), None)
        if level_no is None:
            return False
        current_no = getattr(logging, self.current_log_level, 0) if self.current_log_level else 0
        return self.domain_enabled.get(domain, False) and level_no >= current_no

    def enable_domain(self, domain_name: Union[str, List[str]]):
        if isinstance(domain_name, str):
            domain_name = [domain_name]

        for domain in domain_name:
            if domain not in self.domain_enabled:
                display = None if domain == "" else domain
                raise KeyError(
                    f"domain '{display}' not in {list(self.domain_enabled.keys())}, "
                    f"please choose a supported domain"
                )
            self.domain_enabled[domain] = True

    def disable_domain(self, domain_name: Union[str, List[str]]):
        if isinstance(domain_name, str):
            domain_name = [domain_name]

        for domain in domain_name:
            if domain in self.domain_enabled:
                self.domain_enabled[domain] = False

    # ------------------------------------------------------------------
    # Level management
    # ------------------------------------------------------------------

    def change_log_level(self, level: str):
        level_upper = level.upper() if isinstance(level, str) else None
        level_no = getattr(logging, level_upper, None) if level_upper else None
        if not isinstance(level_no, int):
            display = None if level == "" else level
            raise ValueError(
                f" --- Level '{display}' is not a valid log level, "
                f"defined log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL, "
                f"please select a valid log level"
            )

        # Remove and close previous default (stdout) handler
        if self._default_handler is not None:
            self._logger.removeHandler(self._default_handler)
            self._default_handler.close()

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level_no)
        formatter = CSSFormatter(CSSFormatter.DEFAULT_FORMAT, CSSFormatter.DEFAULT_DATEFMT)
        handler.setFormatter(formatter)
        handler.addFilter(self._domain_filter)
        self._logger.addHandler(handler)
        self._default_handler = handler

        self.current_log_level = level_upper

    # ------------------------------------------------------------------
    # Handler management
    # ------------------------------------------------------------------

    def add_file_handler(self, full_path: Union[str, Path], level_name: str) -> int:
        level_no = getattr(logging, level_name.upper(), None)
        if level_no is None:
            raise ValueError(f"Invalid log level: {level_name}")

        handler = logging.FileHandler(str(full_path))
        handler.setLevel(level_no)
        formatter = CSSFormatter(CSSFormatter.DEFAULT_FORMAT, CSSFormatter.DEFAULT_DATEFMT)
        handler.setFormatter(formatter)
        handler.addFilter(self._domain_filter)
        self._logger.addHandler(handler)

        handler_id = self._next_handler_id
        self._next_handler_id += 1
        self._handlers[handler_id] = handler
        return handler_id

    def add_queue_handler(self, queue, level_name: str) -> int:
        level_no = getattr(logging, level_name.upper(), None)
        if level_no is None:
            raise ValueError(f"Invalid log level: {level_name}")

        handler = handlers.QueueHandler(queue)
        handler.setLevel(level_no)
        handler.addFilter(self._domain_filter)
        self._logger.addHandler(handler)

        handler_id = self._next_handler_id
        self._next_handler_id += 1
        self._handlers[handler_id] = handler
        return handler_id


# ---------------------------------------------------------------------------
# Module-level API -- __log is the hidden singleton
# ---------------------------------------------------------------------------

__log = CSSLogger()


def get_logger(domain: str) -> DomainLogger:
    """Get a domain logger (auto-registers the domain if needed)."""
    return __log.get_logger(domain)


def enable_domain(domain_name: Union[str, List[str]]):
    __log.enable_domain(domain_name)


def disable_domain(domain_name: Union[str, List[str]]):
    __log.disable_domain(domain_name)


def change_log_level(level: str):
    __log.change_log_level(level)


def is_domain_enabled(domain: str, level: str) -> bool:
    return __log.is_domain_enabled(domain, level)


def add_file_handler(full_path: Union[str, Path], level_name: str) -> int:
    return __log.add_file_handler(full_path, level_name)


def add_queue_handler(queue, level_name: str) -> int:
    return __log.add_queue_handler(queue, level_name)


def get_current_log_level() -> Optional[str]:
    return __log.current_log_level


def get_registered_domains() -> List[str]:
    return list(__log.logger_for_domain.keys())
