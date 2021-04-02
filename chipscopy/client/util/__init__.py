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

import code
from typing import Callable
from threading import Condition
from chipscopy import client
from chipscopy.tcf import protocol, peer
from chipscopy.client.util import config  # noqa: F401

# noinspection PyUnresolvedReferences
from chipscopy.tcf.services.remote import (  # noqa: F401
    XicomEverestProxy,
    svfProxy,
    LocatorProxy,
    MemoryProxy,
)

# noinspection PyUnresolvedReferences
from chipscopy.proxies import DebugCoreProxy, DebugCorePollingProxy  # noqa: F401

try:
    import readline

    readline.parse_and_bind("tab: complete")
except Exception as e:
    pass


def start_interactive(local=None):
    console = code.InteractiveConsole(local)
    console.push("from chipscopy.client.util import *")
    console.push("from chipscopy.client.util.config import *")
    console.push("init_config()")
    console.push("from chipscopy.utils.logger import log")
    console.push("from sys import exit")
    console.interact()


def connect_hw(url):
    from .config import init_config

    init_config()
    return client.connect(url)


def get_connections():
    return client.connections()


def process_param_str(params, default_port="3121"):
    parts = params.split(":", 3)
    if len(parts) < 3:
        parts.insert(0, "TCP")
    if len(parts) < 3:
        parts.append(default_port)
    return ":".join(parts)


def parse_params(paramStr):
    args = paramStr.split(":")
    if len(args) != 3:
        raise ValueError("Expected format: <transport>:<host>:<port>")
    transp, host, port = args
    return {
        peer.ATTR_ID: paramStr,
        peer.ATTR_IP_HOST: host,
        peer.ATTR_IP_PORT: port,
        peer.ATTR_TRANSPORT_NAME: transp,
    }


def sync_call(command: Callable, *args, **kwargs):
    """
    Performs a synchronous function call with a done callback that's intended to run on the TCF dispatch thread.
    :param command: Function to be run on the TCF dispatch thread
    :param args: args of function
    :param kwargs: kwargs of function
    :return: Result of function, or exception if error
    """
    cond = Condition()
    call_error = None
    call_result = None

    def done_call(token, error, result):
        nonlocal call_error
        nonlocal call_result
        call_error = error
        call_result = result
        with cond:
            cond.notify()

    kwargs["done"] = done_call
    with cond:
        protocol.invokeLater(command, *args, **kwargs)
        cond.wait()

    if call_error:
        if isinstance(call_error, str):
            call_error = Exception(call_error)
        raise call_error
    return call_result
