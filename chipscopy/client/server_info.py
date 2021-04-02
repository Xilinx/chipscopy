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

import threading
import re
from chipscopy import dm
from chipscopy.dm import memory, jtag, request
from chipscopy.tcf import protocol
from chipscopy.tcf.services import xicom, ServiceSync
from chipscopy.utils.logger import log
from .view_info import ViewInfo
from .util import sync_call, parse_params, process_param_str
from .util import config


class ServerInfo(dm.Node):
    def __init__(self, channel):
        dm.Node.__init__(self, "")
        self.channel = channel
        self._props_ready = threading.Event()
        self._update_static_info()
        self.views = {}

    def __getattr__(self, attr):
        self._props_ready.wait(5)
        return dm.Node.__getattr__(self, attr)

    def __str__(self):
        self._props_ready.wait(5)
        return "ServerInfo({})".format(self.url)

    @property
    def props(self):
        self._props_ready.wait(5)
        return super().props

    def _update_static_info(self):
        if not protocol.isDispatchThread():
            self._props_ready.clear()
            protocol.invokeLater(self._update_static_info)
            return

        self["services"] = self.channel.getRemoteServices()

        peer = self.channel.getRemotePeer()
        self["url"] = "{}:{}".format(peer.getHost(), peer.getPort())

        proc = self.channel.getRemoteService(xicom.XicomService)

        if proc:

            def done_version_info(token, error, results):
                self._props.update(results)
                self._props_ready.set()

            self.add_pending(proc.get_hw_server_version_info(done_version_info))
        else:
            self._props_ready.set()

    def get_sync_service(self, name):
        return ServiceSync(self.channel, name, True)

    def close(self, wait=True):
        if wait:
            protocol.invokeAndWait(self.channel.close)
        else:
            protocol.invokeLater(self.channel.close)
        self.views.clear()

    @staticmethod
    def _check_thread(command, done, *args, **kwargs):
        if not done:
            return sync_call(command, *args, **kwargs)

        kwargs["done"] = done
        if not protocol.isDispatchThread():
            return protocol.invokeAndWait(command, *args, **kwargs)
        return command(*args, **kwargs)

    def connect_remote(self, url: str, done: request.DoneCallback = None):
        """
        Request that the CS Server connect to another server (usually a hw_server)
        :param url: Url for remote server
        :param done: Done callback (skip if calling synchronously)
        :return: Token if async or Results if sync
        """
        return self._check_thread(self._connect_remote, done, url)

    def _connect_remote(self, url, done):
        locator = self.channel.getRemoteService("Locator")

        def done_remote_connect(token, error, result):
            log.client.info(f"{str(self)} connected to {url}")
            done(token, error, result)

        return locator.connect_remote_peer({"ID": url}, done_remote_connect)

    def disconnect_remote(self, url: str, done: request.DoneCallback = None):
        """
        Request that the CS Server disconnect from another server (usually a hw_server)
        :param url: Url for remote server
        :param done: Done callback (skip if calling synchronously)
        :return: Token if async or Results if sync
        """
        return self._check_thread(self._disconnect_remote, done, url)

    def _disconnect_remote(self, url, done):
        locator = self.channel.getRemoteService("Locator")

        def done_remote_disconnect(token, error, result):
            log.client.info(f"{str(self)} disconnected from {url}")
            done(token, error, result)

        return locator.disconnect_remote_peer({"ID": url}, done_remote_disconnect)

    def connect_xvc(
        self,
        xvc_url: str,
        remote_server: str = "",
        idcode: int = 0,
        done: request.DoneCallback = None,
    ):
        """
        Request remote server with XvcContext service to open an XVC connection with given url
        :param xvc_url: XVC Server url address
        :param remote_server: ID of remote server through which to connect
        :param idcode: Optional parameter to force the XVC server to show a specific idcode
        :param done: Done callback (skip if calling synchronously
        :return: Token if async or Results if sync
        """
        params = parse_params(process_param_str(xvc_url, "2225"))
        return self._check_thread(
            self._connect_xvc, done, params["Host"], params["Port"], idcode, remote_server
        )

    def _connect_xvc(
        self,
        xvc_host: str,
        xvc_port: str,
        idcode: int = 0,
        remote_server: str = "",
        done: request.DoneCallback = None,
    ):
        def done_connect_xvc(token, error, result):
            if log.is_domain_enabled("client", "INFO"):
                server = remote_server if remote_server else str(self)
                log.client.info(f"{server} connected to XVC Server {xvc_host}:{xvc_port}")
            done(token, error, result)

        if not remote_server:
            xvc_service = self.channel.getRemoteService("ContextXvc")
            ret = xvc_service.open(xvc_host, xvc_port, idcode, done_connect_xvc)
        else:
            cs_service = self.channel.getRemoteService("ChipScope")
            ret = cs_service.remote_connect_xvc(
                remote_server, xvc_host, xvc_port, idcode, done_connect_xvc
            )
        return ret

    def get_view(self, dm_view):
        dm_name = "chipscopy.dm." + dm_view if isinstance(dm_view, str) else dm_view.__name__
        if dm_name in self.views:
            return self.views[dm_name]

        if isinstance(dm_view, str):
            dm_view = __import__(dm_name, fromlist=[dm_view], globals=globals())
        if not protocol.isDispatchThread():
            manager = protocol.invokeAndWait(dm_view.add_manager_from_channel, self.channel)
        else:
            manager = dm_view.add_manager_from_channel(self.channel)
        view = ViewInfo(manager)
        self.views[dm_name] = view
        return view

    def target(self, target_id=None, cls=dm.Node, index=None, **kwargs):
        view = self.get_view(memory)

        return self._target(view, target_id, cls, index, **kwargs)

    def jtag_target(self, target_id=None, cls=dm.Node, index=None, **kwargs):
        view = self.get_view(jtag)

        return self._target(view, target_id, cls, index, **kwargs)

    def cs_target(self, target_id=None, cls=dm.Node, index=None, **kwargs):
        view = self.get_view("chipscope")

        return self._target(view, target_id, cls, index, **kwargs)

    def dc_target(self, target_id=None, cls=dm.Node, index=None, **kwargs):
        view = self.get_view("debugcore")

        return self._target(view, target_id, cls, index, **kwargs)

    jtarget = jtag_target

    def _target(self, view, target_id=None, cls=dm.Node, index=None, parent=None, **kwargs):
        if target_id is not None:
            ctx = ""
            if type(target_id) is int:
                ctx = view.target_ctx_map[target_id]
            else:
                ctx = target_id

            return view.get_node(ctx, cls)

        if kwargs or parent or cls != dm.Node:

            def match_func(node):
                for key, value in kwargs.items():
                    # if key == "parent" and isinstance(value, dm.Node):
                    #     if value.ctx != node.parent_ctx:
                    #         return False
                    if isinstance(value, str):
                        s = str(getattr(node, key))
                        if not re.search(value, s):
                            return False
                    elif getattr(node, key) != value:
                        return False
                return True

            if parent is not None:
                results = list(filter(match_func, view.get_children(parent)))
            else:
                results = list(filter(match_func, view.get_all()))
            if index is not None:
                return view.get_node(results[index].ctx, cls)
            else:
                nodes = []
                for res in results:
                    nodes.append(view.get_node(res.ctx, cls))
                if len(nodes) == 1:
                    nodes = nodes[0]
                return nodes

        if index is not None:
            parent = view
            return view[parent.children[index]]

        def print_targets(parent=None, level=1):
            for child in view.get_children(parent):
                name = child.Name if child.Name else child.ctx
                print("{}{} {}".format("\t" * level, child.target_id, name))
                print_targets(child, level + 1)

        print_targets()
