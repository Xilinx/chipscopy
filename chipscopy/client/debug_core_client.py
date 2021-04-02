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

from typing import Any, Dict, Generator, Tuple

from chipscopy import dm
from chipscopy.dm import request
from chipscopy.proxies.DebugCoreProxy import DebugCoreService
from chipscopy.tcf.channel import Token


class DebugCoreClientNode(dm.Node):
    """
    This node makes use of the DebugCore service.
    """

    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return not node.parent_ctx

    def read_bytes(
        self,
        address: int,
        data: bytearray,
        offset: int = 0,
        byte_size: int = None,
        done: request.DoneCallback = None,
        progress: request.ProgressCallback = None,
    ) -> Token:
        """
        Reads from memory context, using DebugCore Service.

        Args:
            address (int): Start memory address, to read from.
            data (bytearray): Buffer for return data.
            offset (int): Start byte index *data* buffer, where return data is copied to.
            byte_size (int): Number of byte to read. Default is the size of *data* buffer.
            done (request.DoneCallback):
            progress (request.ProgressCallback):

        Returns: Token
        """

        done = request._make_callback(done)
        initial_token = None
        local_pending = set()
        all_requests_sent = False

        total_read_size = len(data) if byte_size is None else byte_size
        if total_read_size > len(data) - offset:
            raise IndexError("Request to read more data than buffer can hold, from {self.ctx}.")

        chunk_byte_size = 0x8000
        service = self.manager.channel.getRemoteService(DebugCoreService)
        err = None
        seq_it = None

        def get_request_sequence() -> Generator[Tuple[Dict[str, Any], int], None, None]:
            end_addr = address + total_read_size
            for addr, buffer_offset in zip(
                range(address, end_addr, chunk_byte_size),
                range(offset, offset + total_read_size, chunk_byte_size),
            ):
                r_size = chunk_byte_size if addr + chunk_byte_size < end_addr else end_addr - addr
                seq = {"name": "read bytes", "type": "r", "addr": addr, "size": r_size // 4}
                yield seq, buffer_offset

        def request_data() -> Token:
            nonlocal all_requests_sent
            return_token = None

            if err:
                read_done()
                return

            while len(local_pending) < 8:
                seq, buffer_offset = next(seq_it, (None, None))
                if not seq:
                    all_requests_sent = True
                    break
                else:
                    token = service.run_sequence(self.ctx, [seq], receive_data)
                    local_pending.add(token)
                    if not return_token:
                        return_token = token
                    token.data_offset = buffer_offset

            return return_token

        def receive_data(token, error, result):
            nonlocal err

            local_pending.remove(token)
            if err:
                return

            err = error
            if (
                not error
                and hasattr(token, "data_offset")
                and isinstance(result, list)
                and len(result) == 1
                and isinstance(result[0], dict)
            ):
                r_data = result[0]["data"]
                start = token.data_offset
                end = start + len(r_data)
                if end > offset + total_read_size:
                    err = IndexError(
                        "Request to read more data than buffer can hold, from {self.ctx}."
                    )
                else:
                    data[start:end] = r_data
                    if progress:
                        progress((end - offset) / total_read_size)

            if all_requests_sent and not local_pending:
                read_done()
            else:
                request_data()

        def read_done():
            nonlocal initial_token
            token = initial_token
            initial_token = None
            if done:
                done.done_request(token, err, None)

        #
        seq_it = get_request_sequence()
        initial_token = request_data()
        return initial_token

    def write_bytes(
        self,
        address: int,
        data: bytearray,
        offset: int = 0,
        byte_size: int = None,
        done: request.DoneCallback = None,
        progress: request.ProgressCallback = None,
    ) -> Token:
        """
        Read from memory context, using DebugCore Service.

        Args:
            address (int): Start memory address, to write to.
            data (bytearray): Buffer with write data.
            offset (int): Start byte index *data*.
            byte_size (int): Number of byte to write. Default is the size of *data* buffer.
            done (request.DoneCallback):
            progress (request.ProgressCallback):

        Returns: Token
        """

        done = request._make_callback(done)
        initial_token = None
        local_pending = set()
        all_sent = False

        total_write_size = len(data) if byte_size is None else byte_size
        if total_write_size > len(data) - offset:
            raise IndexError("Request to write more data than data buffer size, to {self.ctx}.")

        chunk_byte_size = 0x8000
        service = self.manager.channel.getRemoteService(DebugCoreService)
        err = None
        seq_it = None

        def get_send_sequence() -> Generator[Tuple[Dict[str, Any], int], None, None]:
            end_addr = address + total_write_size
            for addr, buffer_offset in zip(
                range(address, end_addr, chunk_byte_size),
                range(offset, offset + total_write_size, chunk_byte_size),
            ):
                w_size = chunk_byte_size if addr + chunk_byte_size < end_addr else end_addr - addr
                buf = data[buffer_offset : buffer_offset + w_size]
                seq = {"name": "write bytes", "type": "w", "addr": addr, "data": buf}
                yield seq, buffer_offset + w_size

        def send_data() -> Token:
            nonlocal all_sent
            return_token = None

            if err:
                write_done()
                return

            while len(local_pending) < 8 and not all_sent:
                seq, buffer_next_offset = next(seq_it, (None, None))
                if seq:
                    token = service.run_sequence(self.ctx, [seq], send_confirmation)
                    local_pending.add(token)
                    if not return_token:
                        return_token = token
                    token.data_offset = buffer_next_offset
                else:
                    all_sent = True
                    break

            return return_token

        def send_confirmation(token, error, _):
            nonlocal err
            nonlocal all_sent

            local_pending.remove(token)
            if err:
                return

            err = error
            if not error and hasattr(token, "data_offset"):
                buffer_next_offset = token.data_offset
                if progress:
                    progress((buffer_next_offset - offset) / total_write_size)

            if local_pending or not all_sent:
                send_data()
            else:
                write_done()

        def write_done():
            nonlocal initial_token
            token = initial_token
            initial_token = None
            if done:
                done.done_request(token, err, None)

        #
        seq_it = get_send_sequence()
        initial_token = send_data()
        return initial_token
