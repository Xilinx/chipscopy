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

from typing import List, Dict, Any, Iterable
from chipscopy import dm
from chipscopy.dm import request
from chipscopy.utils import words_from_bytes, bytes_from_words, WORD_SIZE
from chipscopy.tcf.services import memory as service
from chipscopy.proxies.ContextXvcProxy import NAME as ContextXvcService
from chipscopy.proxies.DebugCoreProxy import DebugCoreService
from chipscopy.proxies.ProfilerProxy import SERVICE as ProfilerService


class Profiler(object):
    def __init__(self, ctx: str, name: str, capabilities: Dict[str, Any]):
        self.ctx = ctx
        self.name = name
        self.capabilities = capabilities
        self.configuration = {}
        self.data = b""

    def __getitem__(self, item):
        return self.capabilities[item]

    def __setitem__(self, key, value):
        self.configuration[key] = value

    def __str__(self):
        return f"{self.capabilities}"

    def __repr__(self):
        return self.__str__()

    def configure(self, params: Dict[str, Any]):
        self.configuration = params


class MemoryNode(dm.Node):
    """
    Implements memory based transactions for compatible nodes.
    """

    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.AccessTypes and "data" in node.AccessTypes

    def mrd(self, address: int, size: int = 1, done: request.DoneRequest = None):
        """
        Reads requested words from memory context
        :param address: Byte address of starting read
        :param size: Number of words to read
        :param done: Callback when operation complete
        :return: Token of request
        """
        assert done
        done = request._make_callback(done)
        mem = self.mem
        if not mem:
            raise Exception("Could not find memory context for node {}".format(self.ctx))

        address = int(address / WORD_SIZE) * WORD_SIZE
        size *= WORD_SIZE
        mode = service.MODE_CONTINUEONERROR | service.MODE_VERIFY | service.MODE_BYPASS_ADDR_CHECK
        buf = bytearray(size)

        class DoneMemory(service.DoneMemory):
            def doneMemory(self, token, error):
                error = str(error) if error else ""
                if done:
                    done.done_request(token, error, words_from_bytes(buf))

        return mem.get(address, WORD_SIZE, buf, 0, size, mode, DoneMemory())

    def mwr(
        self, address: int, words: List[int] or int, size: int = 1, done: request.DoneRequest = None
    ):
        """
        Writes given words to memory context.
        :param address: Starting byte address of write
        :param words: List of words to write
        :param size: Number of words to write
        :param done: Callback when complete
        :return: Token of request
        """
        assert done
        done = request._make_callback(done)
        mem = self.mem
        if not mem:
            raise Exception("Could not find memory context for node {}".format(self.ctx))

        if isinstance(words, int):
            words = (words,)

        size = max(size, len(words))

        buf = bytes_from_words(words, size)
        address = int(address / WORD_SIZE) * WORD_SIZE
        size *= WORD_SIZE
        mode = service.MODE_CONTINUEONERROR | service.MODE_VERIFY | service.MODE_BYPASS_ADDR_CHECK

        class DoneMemory(service.DoneMemory):
            def doneMemory(self, token, error):
                error = str(error) if error else ""
                if done:
                    done.done_request(token, error, {})

        return mem.set(address, WORD_SIZE, buf, 0, size, mode, DoneMemory())

    def write_bytes(
        self,
        address: int,
        data: bytearray,
        offset: int = 0,
        byte_size: int = None,
        done: request.DoneRequest = None,
    ):
        """
        Writes given words to memory context.
        :param address: Write starting byte address
        :param data: bytearray to write
        :param offset: Start index in *data* to start writing from.
        :param byte_size: Number of bytes to write. Default is size of the *data* buffer.
        :param done: Callback when complete
        :return: Token of request
        """
        assert done
        done = request._make_callback(done)
        mem = self.mem
        if not mem:
            raise Exception(f"Could not find memory context for node {self.ctx}")
        if byte_size is None:
            byte_size = len(data)
        if byte_size > len(data) - offset:
            raise Exception(
                "Request to write more data than provided, to memory context {self.ctx}."
            )

        address = (address // WORD_SIZE) * WORD_SIZE
        mode = service.MODE_CONTINUEONERROR | service.MODE_VERIFY | service.MODE_BYPASS_ADDR_CHECK

        class DoneMemory(service.DoneMemory):
            def doneMemory(self, token, error):
                error = str(error) if error else ""
                if done:
                    done.done_request(token, error, {})

        return mem.set(address, WORD_SIZE, data, offset, byte_size, mode, DoneMemory())

    def get_profilers(self) -> Dict[str, Any] or request.CsFuture:
        assert request
        service = self.manager.channel.getRemoteService(ProfilerService)

        def done_get_capabilities(token, error, results):
            # check if canceled
            if not self.request:
                return

            # check for error or positive result
            if error:
                self.request.set_exception(error)
            else:
                profilers = {key: Profiler(self.ctx, key, value) for key, value in results.items()}
                self.request.set_result(profilers)

        service.get_capabilities(self.ctx, done_get_capabilities)

    def run_profilers(self, profilers: Iterable):
        assert request
        service = self.manager.channel.getRemoteService(ProfilerService)
        params = {p.name: p.configuration for p in profilers}

        def done_configure(token, error, results):
            # check if canceled
            if not self.request:
                return

            # check for error or positive result
            if error:
                self.request.set_exception(error)
            else:
                self.request.set_result(results)

        service.configure(self.ctx, params, done_configure)

    def stop_profilers(self, profilers: Iterable[Profiler]):
        assert request
        service = self.manager.channel.getRemoteService(ProfilerService)
        params = {p.name: {} for p in profilers}

        def done_configure(token, error, results):
            # check if canceled
            if not self.request:
                return

            # check for error or positive result
            if error:
                self.request.set_exception(error)
            else:
                self.request.set_result(results)

        service.configure(self.ctx, params, done_configure)

    def read_profilers(self, profilers: Iterable[Profiler]):
        assert request
        service = self.manager.channel.getRemoteService(ProfilerService)

        def done_read(token, error, results):
            # check if canceled
            if not self.request:
                return

            # check for error or positive result
            if error:
                self.request.set_exception(error)
            else:
                for p in profilers:
                    p.data = results
                self.request.set_result(None)

        service.read(self.ctx, done_read)


def open_xvc(cs_manager: dm.CsManager, host: str, port: str, done: request.DoneCallback):
    """
    Connects to XVC server and opens the XVC Memory Context
    :param cs_manager: Memory Context View Manager
    :param host: Host name or IP Address of XVC Server
    :param port: Port of XVC Server
    :param done: Callback when complete
    :return: Token of request
    """
    proc = cs_manager.channel.getRemoteService(ContextXvcService)
    done = request._make_callback(done)

    # link the ContextXvcService callback directly to this function's callback
    # since we don't need to do any post processing
    return proc.open(host, port, done.done_request)


class XvcNode(MemoryNode):
    """
    Implements functionality to open and close an XVC Memory Context.
    It inherits from MemoryNode to also support mrd and mwr.
    """

    @staticmethod
    def is_compatible(node):
        return node.Name and "XVC" in node.Name and super(XvcNode, XvcNode).is_compatible(node)

    def close(self, done: request.DoneCallback):
        """
        Closes an XVC Memory Context and disconnects from the XVC server
        :param done: Callback when complete
        :return: Token of request
        """
        proc = self.manager.channel.getRemoteService(ContextXvcService)
        done = request._make_callback(done)
        node = self

        def done_cmd(token, error, args):
            node.remove_pending(token)  # done state change
            done.done_request(token, error, args)

        # add pending to indicate that this node is being changed
        return self.add_pending(proc.close(self.ctx, done=done_cmd))
