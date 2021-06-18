# *****************************************************************************
# * Copyright (c) 2011, 2013 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""
ChannelProxy implements forwarding of TCF messages between two channels.
The class is used to implement Locator service "redirect" command.
"""

from .. import channel


class ProxyCommandListener(channel.CommandListener):
    def __init__(self, ch, tokens):
        self.ch = ch
        self.tokens = tokens

    def progress(self, token, data):
        self.ch.sendProgress(self.tokens.get(token), data)

    def result(self, token, data):
        self.ch.sendResult(self.tokens.pop(token, None), data)

    def terminated(self, token, error):
        self.ch.rejectCommand(self.tokens.pop(token, None))


class ChannelProxy(object):
    def __init__(self, x, y):
        # assert not isinstance(x, ChannelLoop)
        # assert not isinstance(y, ChannelLoop)
        self.ch_x = x
        self.ch_y = y
        assert self.ch_x.getState() == channel.STATE_OPEN
        assert self.ch_y.getState() == channel.STATE_OPENING
        self.tokens_x = {}
        self.tokens_y = {}
        cmd_listener_x = ProxyCommandListener(self.ch_x, self.tokens_x)
        cmd_listener_y = ProxyCommandListener(self.ch_y, self.tokens_y)
        proxy = self

        class ProxyX(channel.Proxy):
            def onChannelClosed(self, error):
                proxy.closed_x = True
                if proxy.closed_y:
                    return
                if error is None:
                    proxy.ch_y.close()
                else:
                    proxy.ch_y.terminate(error)

            def onCommand(self, token, service, name, data):
                if proxy.closed_y:
                    return
                assert proxy.ch_y.getState() == channel.STATE_OPEN
                s = proxy.ch_y.getRemoteService(service)
                if not s:
                    proxy.ch_x.terminate(IOError("Invalid service name"))
                else:
                    key = proxy.ch_y.sendCommand(s, name, data, cmd_listener_x)
                    proxy.tokens_x[key] = token

            def onEvent(self, service, name, data):
                s = proxy.ch_x.getRemoteService(service)
                if not s:
                    proxy.ch_x.terminate(IOError("Invalid service name"))
                elif not proxy.closed_y:
                    proxy.ch_y.sendEvent(s, name, data)

        class ProxyY(channel.Proxy):
            def onChannelClosed(self, error):
                proxy.closed_y = True
                if proxy.closed_x:
                    return
                if error is None:
                    proxy.ch_x.close()
                else:
                    proxy.ch_x.terminate(error)

            def onCommand(self, token, service, name, data):
                if proxy.closed_x:
                    return
                assert proxy.ch_x.getState() == channel.STATE_OPEN
                s = proxy.ch_x.getRemoteService(service)
                if not s:
                    proxy.ch_y.terminate(IOError("Invalid service name"))
                else:
                    key = proxy.ch_x.sendCommand(s, name, data, cmd_listener_y)
                    proxy.tokens_y[key] = token

            def onEvent(self, service, name, data):
                s = proxy.ch_y.getRemoteService(service)
                if not s:
                    proxy.ch_y.terminate(IOError("Invalid service name"))
                elif not proxy.closed_x:
                    proxy.ch_x.sendEvent(s, name, data)

        proxy_x = ProxyX()
        proxy_y = ProxyY()

        try:
            self.ch_y.setProxy(proxy_y, self.ch_x.getRemoteServices())

            class ChannelListener(channel.ChannelListener):
                def onChannelClosed(self, error):
                    proxy.ch_y.removeChannelListener(self)
                    if error is None:
                        error = Exception("Channel closed")

                def onChannelOpened(self):
                    proxy.ch_y.removeChannelListener(self)
                    try:
                        proxy.ch_x.setProxy(proxy_x,
                                            proxy.ch_y.getRemoteServices())
                    except IOError as e:
                        proxy.ch_x.terminate(e)
                        proxy.ch_y.terminate(e)
            self.ch_y.addChannelListener(ChannelListener())
        except IOError as e:
            self.ch_x.terminate(e)
            self.ch_y.terminate(e)
