import pytcf

SERVICE_NAME = "Locator"

_waiting_for_disconnect = {}


def get_channels(token, channel):
    args = pytcf.read_command_args(channel)
    pytcf.write_response_args(token, channel, None, ([c.url for c in pytcf.get_channels()],))


def connect_peer(token, channel):
    args = pytcf.read_command_args(channel)

    if len(args) < 1:
        pytcf.write_response_args(token, channel, pytcf.ERR_INV_CONTEXT)
        return

    attr = args[0]
    url = ""
    if type(attr) == dict:
        url = attr.get("ID")
    elif type(attr) == str:
        url = attr

    if not url:
        pytcf.write_response_args(token, channel, pytcf.ERR_INV_CONTEXT)
        return

    target = pytcf.get_channel_from_url(url)
    if target:
        # target.add_linked_channel(channel)
        pytcf.write_response_args(token, channel, None, (target.url,))
        return

    def connect_done(req):
        err = None
        target = pytcf.get_channel_from_url(req.url)
        if target:
            # target.add_linked_channel(channel)
            pass
        else:
            err = pytcf.errno
        pytcf.write_response_args(token, channel, err, (target.url,))

    pytcf.connect_tcf(url, done=connect_done)


def disconnect_peer(token, channel):
    args = pytcf.read_command_args(channel)

    if len(args) < 1:
        pytcf.write_response_args(token, channel, pytcf.ERR_INV_CONTEXT)
        return

    attr = args[1]
    url = ""
    if type(attr) == dict:
        url = attr.get("ID")
    elif type(attr) == str:
        url = attr

    target = pytcf.get_channel_from_url(url)
    if not target:
        pytcf.write_response_args(token, channel, pytcf.ERR_INV_CONTEXT)
        return

    def peer_disconnected():
        pytcf.write_response_args(token, channel, None, (True,))

    _waiting_for_disconnect[target] = peer_disconnected
    pytcf.disconnect_channel(target)


def channel_closed(channel):
    channels = list(pytcf.get_channels())
    for c in channels:
        if channel in c.linked_channels:
            c.linked_channels.remove(channel)
            if not c.linked_channels:
                pytcf.disconnect_channel(c)

    f = _waiting_for_disconnect.get(channel)
    if f:
        f()


def ini_service(si):
    pytcf.add_command_handler(si, SERVICE_NAME, "getChannels", get_channels)
    pytcf.add_command_handler(si, SERVICE_NAME, "connectPeer", connect_peer)
    pytcf.add_command_handler(si, SERVICE_NAME, "disconnectPeer", disconnect_peer)
    pytcf.add_channel_close_listener(channel_closed)