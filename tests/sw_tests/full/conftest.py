# Copyright (c) 2020 Xilinx,Inc.
# All rights reserved.
#
# This file contains confidential and proprietary information
# of Xilinx, Inc. and is protected under U.S. and
# international copyright and other intellectual property
# laws.
#
# DISCLAIMER
# This disclaimer is not a license and does not grant any
# rights to the materials distributed herewith. Except as
# otherwise provided in a valid license issued to you by
# Xilinx, and to the maximum extent permitted by applicable
# law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
# WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
# AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
# BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
# INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
# (2) Xilinx shall not be liable (whether in contract or tort,
# including negligence, or under any other theory of
# liability) for any loss or damage of any kind or nature
# related to, arising under or in connection with these
# materials, including for any direct, or any indirect,
# special, incidental, or consequential loss or damage
# (including loss of data, profits, goodwill, or any type of
# loss or damage suffered as a result of any action brought
# by a third party) even if such damage or loss was
# reasonably foreseeable or Xilinx had been advised of the
# possibility of the same.
#
# CRITICAL APPLICATIONS
# Xilinx products are not designed or intended to be fail-
# safe, or for use in any application requiring fail-safe
# performance, such as life-support or safety devices or
# systems, Class III medical devices, nuclear facilities,
# applications related to the deployment of airbags, or any
# other applications that could lead to death, personal
# injury, or severe property or environmental damage
# (individually and collectively, "Critical
# Applications"). Customer assumes the sole risk and
# liability of any use of Xilinx products in Critical
# Applications, subject only to applicable laws and
# regulations governing limitations on product liability.
#
# THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
# PART OF THIS FILE AT ALL TIMES.

# import sys
# import os
# import pytest
# import socket
# from chipscopy.tcf import protocol, connect, process_param_str
# from chipscopy.tcf.services import ServiceSync
# from chipscopy.client import server_info
# from chipscopy import xvc
#
# sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))
#
#
# def pytest_addoption(parser):
#     parser.addoption('--hw_server', metavar='<hw_server url>', type=str, default='',
#                      help='Url for Hardware Server (default TCP:127.0.0.1:3121)')
#     parser.addoption('--cs_server', metavar='<cs_server url>', type=str, default='',
#                      help='Url for Chipscope Server (default TCP:127.0.0.1:3042)')
#     parser.addoption('--hostname', metavar='<hostname>', type=str, default=socket.gethostname(),
#                      help='Override hostname to support docker testing')
#
# @pytest.fixture(scope="session")
# def tcf_event_queue():
#     protocol.startEventQueue()
#
#
# @pytest.fixture(scope="session")
# def hw_channel(request, tcf_event_queue):
#     url = request.config.getoption("hw_server")
#     if not url:
#         return pytest.skip("hw_server url not set")
#     url = process_param_str(url)
#     return connect(url)
#
#
# @pytest.fixture(scope="session")
# def cs_channel(request, tcf_event_queue):
#     url = request.config.getoption("cs_server")
#     if not url:
#         return pytest.skip("cs_server url not set")
#     url = process_param_str(url)
#     c = connect(url)
#     yield c
#     test_service = ServiceSync(c, "Test")
#     test_service.exit()
#
#
# @pytest.fixture(scope="session")
# def cs_hw_channel(cs_channel, hw_channel):
#     locator_service = ServiceSync(cs_channel, "Locator")
#     locator_service.connect_remote_peer({"ID": hw_channel.remote_peer.getID()}).get()
#     return cs_channel
#
#
# @pytest.fixture()
# def cs_xvc_server(request, cs_hw_channel, hw_channel):
#     node = None
#     server = None
#     cs_service = None
#
#     def start_server(handler, port=2222):
#         nonlocal node
#         nonlocal server
#         nonlocal cs_service
#
#         hostname = request.config.getoption("hostname")
#
#         tear_down()
#         server = xvc.XVCServer(port, handler)
#         server.start(2)
#
#         css = server_info.ServerInfo(cs_hw_channel)
#         cs_view = css.get_view("chipscope")
#         cs_service = css.get_sync_service("ChipScope")
#
#         # NOTE - Useful for when on VPN.
#         if hostname.upper() == socket.gethostname().upper():
#             hostname = "localhost"
#
#         cs_service.remote_connect_xvc(hw_channel.remote_peer.getID(), hostname, str(port)).get()
#
#         nodes = filter(lambda x: "XVC" in x.Name, cs_view.get_children())
#
#         try:
#             node = next(nodes)
#         except StopIteration:
#             node = None
#         return node, css
#
#     def tear_down():
#         nonlocal node
#         nonlocal cs_service
#         nonlocal server
#         if node and cs_service:
#             cs_service.remote_disconnect_xvc(node.ctx).get()
#             node = None
#             cs_service = None
#         if server:
#             server.stop()
#
#     request.addfinalizer(tear_down)
#     return start_server
