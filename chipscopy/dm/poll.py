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

from typing import NewType, Callable, Dict
from chipscopy.proxies import DebugCorePollingProxy as proxy
from chipscopy.dm import request
from chipscopy.tcf import protocol

PollEventHandler = NewType("PollEventHandler", Callable[[str, Dict], None])


class DebugCorePollScheduler(object):
    """
    Handles scheduling of DebugCore polls and maintains list of current available polls.

    Iterate through list of current polls via get_polls(<parent_node_ctx>)

    It's best to retain the poll_ctx and access the poll description through the scheduler.

    .. method:: poll = scheduler[poll_ctx]

        Gets poll for a given context id
    """

    def __init__(self, channel):
        assert protocol.isDispatchThread()
        self.serv = channel.getRemoteService(proxy.NAME)
        self.polls = {}
        self.nodes = {}
        scheduler = self

        class DebugCorePollingListener(proxy.DebugCorePollingListener):
            def poll_added(self, props: proxy.DebugCorePoll):
                scheduler._add_poll(props)

            def poll_removed(self, poll_ctx: str):
                scheduler._remove_poll(poll_ctx)

            def poll_event(self, poll_ctx: str, props: Dict):
                poll = scheduler.polls.get(poll_ctx)
                if poll and "event_listeners" in poll:
                    for event_listener in poll["event_listeners"]:
                        event_listener(poll, props)

        self.serv.add_listener(DebugCorePollingListener())

    def _add_poll(self, poll):
        poll_id = poll.get("ID")
        parent_id = poll.get("parentID")
        if poll_id:
            self.polls[poll["ID"]] = poll
            if parent_id:
                if parent_id not in self.nodes:
                    self.nodes[parent_id] = set()
                self.nodes[parent_id].add(poll_id)

    def _remove_poll(self, poll_ctx):
        if poll_ctx in self.polls:
            parent_id = self.polls[poll_ctx].get("parentID")
            if parent_id:
                self.nodes[parent_id].remove(poll_ctx)
            del self.polls[poll_ctx]

    def _add_event_listener(self, poll_id, event_handler: PollEventHandler):
        poll = self.polls[poll_id]
        if "event_listeners" not in poll:
            poll["event_listeners"] = set()
        poll["event_listeners"].add(event_handler)

    def _remove_event_listener(self, poll_id, event_handler: PollEventHandler):
        poll = self.polls[poll_id]
        if "event_listeners" in poll:
            try:
                poll["even_listeners"].remove(event_handler)
            except KeyError:
                pass

    def _retain_poll(self, poll_id):
        poll = self.polls[poll_id]
        if "ref_count" not in poll:
            poll["ref_count"] = 1
        else:
            poll["ref_count"] += 1

    def _release_poll(self, poll_id):
        assert self._get_ref_count(poll_id) > 0
        poll = self.polls[poll_id]
        poll["ref_count"] -= 1
        return poll["ref_count"]

    def _get_ref_count(self, poll_id):
        poll = self.polls[poll_id]
        return poll.get("ref_count", 0)

    def update_polls(self, node_id: str = "", done: request.DoneCallback = None) -> request.Token:
        pending = set()
        ret_token = None

        def done_poll_update(token, error, poll):
            pending.remove(token)
            self._add_poll(poll)
            if not pending and done:
                if node_id:
                    results = self.nodes[node_id]
                else:
                    results = self.polls.keys()
                done(ret_token, error, results)

        def done_get_polls(token, error, poll_ids):
            pending.remove(token)
            if not error:
                for poll_id in poll_ids:
                    pending.add(self.serv.get_context(poll_id, done_poll_update))
            if not pending and done:
                done(ret_token, None, [])

        ret_token = self.serv.get_polls(node_id, done_get_polls)
        pending.add(ret_token)
        return ret_token

    def __getitem__(self, item):
        return self.polls[item]

    def get_polls(self, node_id: str = None) -> proxy.DebugCorePoll:
        """
        Poll iterator given a parent debug core node id

        :param node_id: DebugCore context id
        :return: iterator of polls
        """
        if node_id:
            if node_id not in self.nodes:
                raise Exception("Invalid Node Context")
            for poll_id in self.nodes[node_id]:
                yield self.polls[poll_id]
        else:
            for poll in self.polls.values():
                yield poll

    def get_poll_name(self, poll_id: str) -> str:
        if poll_id in self.polls:
            poll = self.polls[poll_id]
            poll_name = poll["name"]
            return poll_name
        else:
            raise Exception(f"Poll ID cannot be found: {poll_id}")

    def schedule_poll(
        self,
        node_ctx: str,
        seq: proxy.DebugCoreSequence,
        name: str = "",
        period: int = 1000,
        event_handler: PollEventHandler = None,
        done: request.DoneCallback = None,
    ) -> request.Token:
        """
        Schedules a poll with the DebugCorePolling Service

        :param node_ctx: Node context to poll
        :param seq: DebugCore sequence to run at each poll
        :param name: Name of the poll
        :param period: Minium period between polls (ms)
        :param event_handler: Event handler when poll conditions are met
        :param done: Done handler called when poll is registered
        :return: Token for poll registration
        """

        def done_add_poll(token, error, poll_id):
            if not error:
                if event_handler:
                    self._add_event_listener(poll_id, event_handler)
                self._retain_poll(poll_id)
            if done:
                done(token, error, poll_id)

        poll = {"name": name, "period": period, "seq": seq}
        return self.serv.add_poll(node_ctx, poll, done_add_poll)

    def release_poll(
        self,
        poll_ctx: str,
        event_handler: PollEventHandler = None,
        done: request.DoneCallback = None,
    ) -> request.Token:
        """
        Removes a scheduled poll.

        :param poll_ctx: Poll context id
        :param event_handler: Event handler to release.
        :param done: Done handler when complete
        :return: Token for removal
        """
        if event_handler:
            self._remove_event_listener(poll_ctx, event_handler)

        ref_count = self._release_poll(poll_ctx)

        if not ref_count:
            return self.serv.remove_poll(poll_ctx, done)

        t = request.Token()

        if done:
            protocol.invokeLater(done, t, None, None)

        return t

    def retain_poll(
        self,
        poll_ctx: str,
        event_handler: PollEventHandler = None,
        done: request.DoneCallback = None,
    ) -> request.Token:
        """
        Retains a poll so it's not lost if released elsewhere.  Also, this subscribes a new PollEventHandler if
        given.

        :param poll_ctx: Poll context ID
        :param event_handler: Event handler that responds to a poll event
        :param done: Done retain callback
        :return: Token of request
        """

        assert poll_ctx in self.polls

        def done_retain(token, error, result):
            if not error:
                if event_handler:
                    self._add_event_listener(poll_ctx, event_handler)
                self._retain_poll(poll_ctx)
            if done:
                done(token, error, result)

        if self._get_ref_count(poll_ctx):
            # This scheduler already has subscribed to the hw_server so no need to send a TCF message
            t = request.Token()
            if done:
                protocol.invokeLater(done_retain, t, None, None)
            return t

        return self.serv.retain_poll(poll_ctx, done_retain)
