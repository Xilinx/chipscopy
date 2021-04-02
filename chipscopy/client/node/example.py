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

from typing import List
from chipscopy import dm
from chipscopy.dm import request
from chipscopy.dm.chipscope import ChipScopeManager
from chipscopy.tcf import protocol


class ExampleMemNode(dm.Node):
    @staticmethod
    def is_compatible(node: "Node"):
        if not node.manager:
            return node.type
        if not node.parent:
            return True
        parent = node.manager[node.parent]
        if parent.type and parent.type == "debug_hub":  # does not work for cores under a DebugHub
            return False
        return isinstance(node.manager, ChipScopeManager)

    def post_init(self):
        self["mem_setup"] = True
        if self.dud_was_here:
            self["dud_was_here"] = False

        self.mrd(0x100, done=self.default_done())  # implicitly initializes node in cs_server

    def default_done(self, done=None):
        def done_cmd(token, error, results):
            self.remove_pending(token)
            if done:
                done(token, error, results)

        return done_cmd

    def get_example_service(self):
        if not self.manager:
            raise Exception("Unable to run memory operation")

        service = self.manager.channel.getRemoteService("Example")

        if not service:
            raise Exception("Example Service not supported in server")

        return service

    def mrd(self, addr: int, word_count: int = 1, done: request.DoneCallback = None):
        service = self.get_example_service()
        return self.add_pending(service.mrd(self.ctx, addr, word_count, self.default_done(done)))

    def mwr(
        self, addr: int, words: List[int], word_count: int = 0, done: request.DoneCallback = None
    ):
        service = self.get_example_service()
        return self.add_pending(
            service.mwr(self.ctx, addr, words, word_count, self.default_done(done))
        )


class ExampleDudNode(dm.Node):
    def __init__(self):
        super().__init__()
        self.duded = 0

    @staticmethod
    def is_compatible(node: "Node"):
        return (not node.manager) or isinstance(node.manager, ChipScopeManager)

    def post_init(self):
        self["dud_was_here"] = True
        self.duded += 1
        self["duded"] = self.duded

    @staticmethod
    def default_done(done=None):
        def done_cmd(token, error, results):
            if done:
                done(token, error, results)

        return protocol.invokeLater(done_cmd)

    def mrd(self, addr: int, word_count: int = 1, done: request.DoneCallback = None):
        return self.default_done(done)

    def mwr(
        self, addr: int, words: List[int], word_count: int = 0, done: request.DoneCallback = None
    ):
        return self.default_done(done)
