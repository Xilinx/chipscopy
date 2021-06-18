# *****************************************************************************
# * Copyright (c) 2011, 2013-2014, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""
Simple interactive shell for TCF.  This is basically a Python interpreter with
a few TCF extensions.

Usage:
    python -m tcf.shell

Commands:
    peers              - Print discovered peers
    connect(params)    - Connect to TCF peer, params =
                         "<protocol>:<host>:<port>"
    cmd.<service>.<command<(args)
                       - Send command to remote service and return result
    disconnect         - Disconnect from peer
    events.record(<service>)
                       - Start recording events for service
    events             - Print last recorded events
    events.stop([<service>])
                       - Stop recording for service or for all services
"""

import code
import os
import sys


try:
    import tcf
except ImportError:
    # add parent dir to path
    sys.path.insert(0, os.path.dirname(os.getcwd()))
    import tcf

from tcf.util import sync, event  # @UnresolvedImport
from tcf import protocol, channel  # @UnresolvedImport


class print_peers:
    "Print list of discovered peers"
    def __call__(self):
        return tcf.peers()

    def __repr__(self):
        peers = tcf.peers()
        return '\n'.join(["%s, %s" % (p.getID(), p.getName())
                          for p in list(peers.values())])


class Shell(code.InteractiveConsole, protocol.ChannelOpenListener,
            channel.ChannelListener):
    def __init__(self):
        locals = {  # @ReservedAssignment
            "connect": tcf.connect,
            "peers": print_peers()
        }
        protocol.startEventQueue()
        protocol.startDiscovery()
        protocol.invokeAndWait(protocol.addChannelOpenListener, self)
        code.InteractiveConsole.__init__(self, locals)

    def interact(self, banner=None):
        try:
            try:
                ps1 = sys.ps1  # @UndefinedVariable
            except AttributeError:
                ps1 = None
            sys.ps1 = "tcf> "
            super(Shell, self).interact(banner)
        finally:
            if ps1:
                sys.ps1 = ps1
            else:
                del sys.ps1
            protocol.invokeLater(protocol.removeChannelOpenListener, self)
            protocol.shutdownDiscovery()
            protocol.getEventQueue().shutdown()

    def onChannelOpen(self, channel):
        wrapper = sync.DispatchWrapper(channel)
        self.locals["channel"] = wrapper
        self.locals["disconnect"] = wrapper.close
        self.locals["cmd"] = sync.CommandControl(channel, interactive=True)
        self.locals["events"] = event.EventRecorder(channel)
        protocol.invokeAndWait(protocol.removeChannelOpenListener, self)
        wrapper.addChannelListener(self)

    def onChannelClosed(self, error):
        del self.locals["channel"]
        del self.locals["cmd"]
        del self.locals["disconnect"]
        del self.locals["events"]
        protocol.addChannelOpenListener(self)


def interact():
    shell = Shell()
    try:
        # enable commandline editing if available
        import readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.set_completer(rlcompleter.Completer(shell.locals).complete)
        readline.parse_and_bind("tab: complete")
    shell.interact("TCF Shell")

if __name__ == "__main__":
    interact()
