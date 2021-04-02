# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

import socket
import time


DISCOVERY_TCF_PORT = 1534
TCF_VERSION = '2'
UDP_REQ_INFO = 1
UDP_PEER_INFO = 2
UDP_REQ_SLAVES = 3
UDP_SLAVES_INFO = 4
UDP_PEERS_REMOVED = 5


class ServerPeer(object):
    def __init__(self, address, name):
        self.address = address
        self.name = name

    def get_address(self):
        return self.address

    def get_name(self):
        return self.name

    def __str__(self):
        return '{}, {}'.format(self.address, self.name)


NAME_ATTR = 'Name'
TRANSPORT_ATTR = 'TransportName'
HOST_ATTR = 'Host'
PORT_ATTR = 'Port'


def find_peers(timeout=5):
    peers = []

    header = bytearray([ord('T'), ord('C'), ord('F'), ord(TCF_VERSION), UDP_REQ_INFO, 0, 0, 0])
    bcast_addr = '<broadcast>'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', 0))  # use local ip address and random port

    sock.sendto(bytes(header), (bcast_addr, DISCOVERY_TCF_PORT))

    peer_packets = []
    t_end = time.time() + timeout
    print('Searching for servers for {} seconds.  Please wait...'.format(timeout))
    while time.time() < t_end:
        data, address = sock.recvfrom(1024)
        recv_header = list(data[:8].decode('utf-8'))
        req_type = ord(recv_header[4])
        recv_data = data[8:].decode('utf-8')
        if req_type == UDP_PEER_INFO and len(recv_data) > 0:
            peer_packets.append(recv_data)

    for packet in peer_packets:
        peer_attrs = packet.split('\0')
        peer_name = ''
        peer_transport = ''
        peer_host = ''
        peer_port = ''
        for attr in peer_attrs:
            if '=' not in attr:
                continue
            key, value = attr.split('=', 1)
            if key == NAME_ATTR:
                peer_name = value
            elif key == TRANSPORT_ATTR:
                peer_transport = value
            elif key == HOST_ATTR:
                peer_host = value
            elif key == PORT_ATTR:
                peer_port = value
        peer_addr = peer_transport + ':' + peer_host + ':' + peer_port
        dup_peer = False
        for peer in peers:
            if peer.get_address() == peer_addr and peer.get_name() == peer_name:
                dup_peer = True
                break
        if not dup_peer:
            peers.append(ServerPeer(peer_addr, peer_name))

    return peers

