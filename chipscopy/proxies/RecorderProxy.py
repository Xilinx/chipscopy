# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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


from typing import ByteString, Dict, Any
from chipscopy.tcf.services import Service, DoneHWCommand, Token

NAME = "Recorder"
"""Recorder service name."""


class RecorderProxy(Service):
    """TCF Recorder service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def start_recorder(self, name: str, done: DoneHWCommand = None) -> Token:
        """
        Start TCF Recording

        :param name: Name of recording
        :param done: Callback with result and any error.
        """
        return self.send_xicom_command("startRecorder", (name,), done)

    def stop_recorder(self, name: str = "", done: DoneHWCommand = None) -> Token:
        """
        Stop TCF Recording

        :param name: Name of recording
        :param done: Callback with result and any error.
        """
        return self.send_xicom_command("stopRecorder", (name,), done)

    def start_playback(self, name: str, done: DoneHWCommand = None) -> Token:
        """
        Start TCF Recording

        :param name: Name of recording
        :param done: Callback with result and any error.
        """
        return self.send_xicom_command("startPlayback", (name,), done)

    def stop_playback(self, name: str = "", done: DoneHWCommand = None) -> Token:
        """
        Stop TCF Recording

        :param name: Name of recording
        :param done: Callback with result and any error.
        """
        return self.send_xicom_command("stopPlayback", (name,), done)
