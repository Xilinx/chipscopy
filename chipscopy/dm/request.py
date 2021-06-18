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

import collections
import threading
import inspect
from typing import Type, Callable, NewType, Any
from chipscopy.tcf import protocol
from chipscopy.tcf.channel import Token
from chipscopy.utils.logger import log
from . import Node, CsManager


def get_request_queue(cs_manager, queue_group):
    if not cs_manager.request_queue:
        cs_manager.request_queue = {queue_group: RequestQueue()}
    elif queue_group not in cs_manager.request_queue.keys():
        cs_manager.request_queue[queue_group] = RequestQueue()

    return cs_manager.request_queue[queue_group]


class DoneRequest(object):
    def done_request(self, token, error, result):
        pass

    def __call__(self, token, error, results):
        self.done_request(token, error, results)


class ProgressRequest(object):
    def done_progress(self, token, error, result):
        pass

    def __call__(self, token, error, results):
        self.done_progress(token, error, results)


DoneCallback = NewType("DoneCallback", DoneRequest or Callable[[Any, str or Exception, Any], None])
ProgressCallback = NewType("ProgressCallback", ProgressRequest or Callable[[float], None])
# Token = NewType("Token", token)


class GenericCallback(object):
    def __init__(self, callback):
        self.callback = callback

    def __getattr__(self, attr):
        if attr.startswith("done"):
            return self.callback


def _make_callback(done):
    if inspect.isfunction(done) or inspect.ismethod(done):
        return GenericCallback(done)
    return done


class RequestQueue(object):
    def __init__(self):
        self.deq = collections.deque()

    def add(self, req):
        self.deq.append(req)

    def is_first(self, req):
        return req == self.deq[0]

    def done_request(self, req):
        self.deq.remove(req)
        if len(self.deq) > 0:
            next_req = self.deq[0]
            protocol.invokeLater(next_req._invoke)


class CsRequest(object):
    """
    Handles requests for individual nodes managed by a CsManager, ensuring that a particular request is run
    when the node is available.
    """

    def __init__(
        self,
        cs_manager: CsManager,
        node_id: str = "",
        node_cls: Type[Node] = Node,
        done=None,
        progress=None,
    ):
        self.cs_manager = cs_manager
        self.node_id = node_id
        self.node_cls = node_cls
        self.node = None
        self.done = done
        # If the node supports progress update, this member var should have an instance obj of the
        # CsRequestProgressUpdate class
        self.progress = progress
        self.request_queue = None
        self.run_func = self.default_run_func
        self.run_args = ((), {})
        self.result = None
        self.error = ""
        self.called = False

    def get_request_queue(self, node):
        if not self.request_queue:
            queue_group = node.queue_group
            self.request_queue = get_request_queue(self.cs_manager, queue_group)
            self.request_queue.add(self)
        return self.request_queue

    def __getattr__(self, item):
        self.run_func = item
        return self.__call__

    def __call__(self, *args, **kwargs):

        self.run_args = (args, kwargs)
        self.node = None
        self.request_queue = None
        self.result = None
        self.error = None
        self.called = True

        log.request.info(
            f"Starting request {self} {self.cs_manager} {self.node_id} {self.node_cls} {self.run_args}"
        )

        if not protocol.isDispatchThread():
            protocol.invokeLater(self._invoke)
        else:
            self._invoke()
        return self

    def _invoke(self):
        if not self.cs_manager.is_ready:
            log.request.debug(f"cs_manager not ready {self}")
            protocol.invokeLaterWithDelay(1, self._invoke)
            return

        node = self.cs_manager.get_node(self.node_id)

        if not node:
            self.done_run(None, Exception(f"Could not find context for {self.node_id}"), None)
            return

        request_queue = self.get_request_queue(node)

        if not request_queue.is_first(self):
            log.request.info(f"Queuing {self} {node.queue_group}")
            return

        if not node.is_ready:
            log.request.debug(f"Node not ready {self}")
            protocol.invokeLaterWithDelay(1, self._invoke)
            return

        try:
            node = self.cs_manager.get_node(self.node_id, self.node_cls)
        except Exception as e:
            self.error = e
            self.done_run(self, self.error, self.result)
            return

        if not node:
            self.done_run(
                None,
                Exception(f"Could not find context for {self.node_id} of type {self.node_cls}"),
                None,
            )
            return

        if not node.is_ready:
            log.request.debug(f"Node class switch not ready {self}")
            protocol.invokeLaterWithDelay(1, self._invoke)
            return

        self.node = node
        args, kwargs = self.run_args
        try:
            log.request.info(f"Running {self} {self.run}")
            result = self.run(*args, **kwargs)
            if result is not None:
                self.result = result
        except Exception as e:
            # exception_type = type(e).__name__
            # exception_message = e
            # self.error = f"({exception_type}) {exception_message}"
            self.error = e

        if self.called and self.result is not None or self.error:
            self.done_run(self, self.error, self.result)

    def run(self, *args, **kwargs):
        if isinstance(self.run_func, str):
            self.run_func = getattr(self.node, self.run_func)
        done = kwargs.get("done")
        if not done and args and len(inspect.signature(self.run_func).parameters) == len(args):
            done = args[-1]
            args = args[:-1]
        if done:
            self.done = done
        kwargs["done"] = self.done_run

        # NOTE - Only if the progress_update var has a valid CsRequestProgressUpdate instance obj
        #  as its value, add this to the kwargs. Many existing funcs dont expect to get the
        #  "progress_update" argument and error out.
        if self.progress is not None:
            kwargs["progress_update"] = self.progress_update

        if self.run_func:
            log.request.debug(f"Run func {self.run_func} ({args}, {kwargs}")
            self.run_func(*args, **kwargs)
        else:
            self.error = Exception("No run function set for request")

    def done_run(self, token=None, error=None, result=None):
        log.request.info(f"Done Run {self} {error} {result}")
        self.run_func = self.default_run_func
        if self.request_queue:
            self.request_queue.done_request(self)
        if self.done:
            self.done(self, error, result)
        self.called = False

    def progress_update(self, token=None, error=None, result=None):
        log.request.info(f"Progress Update {self} {result}")
        self.run_func = self.default_run_func
        if self.progress:
            self.progress(self, error, result)

    def default_run_func(self, done=None, progress_update=None):
        self.result = self.cs_manager[self.node_id]


class CsRequestSync(CsRequest):
    def __init__(self, cs_manager: CsManager, node_id: str = "", node_cls: Type[Node] = Node):
        cond = threading.Condition()
        req = self

        class DoneSync(DoneRequest):
            def done_request(self, token, error, result):
                req.error = error
                req.result = result
                with cond:
                    cond.notify()

        super(CsRequestSync, self).__init__(cs_manager, node_id, node_cls, DoneSync())
        self.cond = cond

    def __call__(self, *args, **kwargs):
        timeout = None
        if "timeout" in kwargs:
            timeout = kwargs.pop("timeout")

        # If done is passed as None or not passed at all then wait - meaning block until command completes.
        # This could happen with kwargs (done=arg) or with done passed as the last argument in list.
        # These cases are handled:
        # 1. function_call(blah, blah)                <- No done passed at all in list   : Block
        # 2. function_call(blah, blah, None)          <- Done passed as None as last arg : Block
        # 3. function_call(blah, blah, done=None)     <- Done passed as None with kwarg  : Block
        # 4. function_call(blah, blah, done=callback) <- Done callback as kwarg          : Do not block
        # 5. function_call(blah, blah, callback)      <- Done callback as last arg       : Do not block

        should_wait = True  # Case 1,2,3
        if "done" in kwargs and kwargs["done"] is not None:
            # Case 4
            should_wait = False
        elif self.run_func:
            run_func = self.run_func
            if isinstance(run_func, str):
                run_func = getattr(self.node_cls, run_func)
                if run_func and len(args) == len(inspect.signature(run_func).parameters) - 1:
                    if len(args) > 0 and args[len(args) - 1] is not None:
                        # Case 5
                        should_wait = False

        log.request.info(f"Request sync start {self} timeout {timeout}")
        if not should_wait:
            super(CsRequestSync, self).__call__(*args, **kwargs)
            return self

        with self.cond:
            super(CsRequestSync, self).__call__(*args, **kwargs)
            completed = self.cond.wait(timeout)
        log.request.debug(
            f"Request sync done {self.error} {self.result} completed {completed} {self}"
        )
        if self.error:
            if isinstance(self.error, str):
                self.error = Exception(self.error)
            elif isinstance(self.error, dict):
                self.error = Exception(self.error.get("Format"))
            elif not isinstance(self.error, BaseException):
                self.error = Exception(str(self.error))
            raise self.error
        elif not completed:
            raise Exception("Request timed out.")
        return self.result


class CancelError(Exception):
    pass


DoneFutureCallback = NewType("DoneFutureCallback", Callable[["CsFuture"], None])
ProgressFutureCallback = NewType("ProgressFutureCallback", Callable[["CsFuture"], None])


def null_callback(future):
    pass


class CsFuture(object):
    def __init__(self, done=None, progress=None, final=None):
        self._done_callback = CsFuture._wrap_callback(done)
        self._progress_callback = CsFuture._wrap_callback(progress)
        self.is_done = False
        self._result = None
        self._error = None
        self._progress_status = None
        self.final = final

    def unset(self):
        self.is_done = False
        self._result = None
        self._error = None

    @staticmethod
    def _wrap_callback(done):
        if not done:
            return done

        if inspect.isfunction(done) or inspect.ismethod(done):
            sig = inspect.signature(done)
            if len(sig.parameters) == 1:
                return done

        # done = _make_callback(done)

        def done_oldcallback(future: CsFuture):
            done(future, future._error, future._result)

        return done_oldcallback

    def _sanitize_error(self):
        if isinstance(self._error, str):
            self._error = Exception(self._error)
        elif isinstance(self._error, dict):
            self._error = Exception(self.error.get("Format"))

    def _finalize(self):
        if self.final and not protocol.isDispatchThread():
            final = self.final
            self.final = None
            final(self)

    @property
    def result(self):
        if not self.is_done:
            raise Exception("CsFuture not done")
        if self._error:
            self._sanitize_error()
            raise self._error
        self._finalize()
        return self._result

    @property
    def progress(self):
        if self._error:
            self._sanitize_error()
            raise self._error
        return self._progress_status

    @property
    def error(self):
        if not self.is_done:
            raise Exception("CsFuture not done")
        self._sanitize_error()
        self._finalize()
        return self._error

    def _invoke_done(self):
        self.is_done = True
        if self._done_callback:
            self._done_callback(self)

    def _invoke_progress(self):
        if self._progress_callback:
            self._progress_callback(self)

    def set_result(self, result):
        self._result = result
        self._invoke_done()

    def set_progress(self, progress_status):
        self._progress_status = progress_status
        self._invoke_progress()

    def set_exception(self, error):
        self._error = error
        self._invoke_done()

    def cancel(self):
        if not self._error:
            self.set_exception(CancelError("Request Cancelled"))

    @property
    def handle_old_done(self):
        future = self

        def old_done_handler(token, error, result):
            if error:
                future.set_error(error)
            else:
                future.set_result(result)

        return old_done_handler


class CsFutureSync(CsFuture):
    def __init__(self, done=None, timeout=None, *args, **kwargs):
        super().__init__(done, *args, **kwargs)
        self.cond = threading.Event()
        self.timeout = timeout

    def _invoke_done(self):
        super()._invoke_done()
        if self.cond:
            self.cond.set()

    @property
    def result(self):
        self.cond.wait(self.timeout)
        return super().result

    @property
    def error(self):
        self.cond.wait(self.timeout)
        return super().error

    def run(self, func, *args, **kwargs):
        if protocol.isDispatchThread():
            func(*args, **kwargs)
        else:
            protocol.invokeLater(func, *args, **kwargs)
        if self.cond:
            return self.result
        return self

    def wait(self, timeout: int = None):
        if protocol.isDispatchThread():
            return
        if timeout is not None:
            self.timeout = timeout
        completed = self.cond.wait(self.timeout)
        log.request.debug(
            f"Request sync done {self._error} {self._result} completed {completed} {self}"
        )
        if not completed and not self._error:
            self.cancel()
            raise Exception("Request timed out.")
        else:
            self._finalize()


class CsFutureRequest(CsFuture):
    """
    Handles requests for individual nodes managed by a CsManager, ensuring that a particular request is run
    when the node is available.
    """

    def __init__(
        self, cs_manager: CsManager, node_id: str = "", node_cls: Type[Node] = Node, *args, **kwargs
    ):
        self.node_cls = node_cls
        super().__init__(*args, **kwargs)
        self.cs_manager = cs_manager
        self.node_id = node_id
        self.node = None
        # If the node supports progress update, this member var should have an instance obj of the
        # CsRequestProgressUpdate class
        self.request_queue = None
        self.run_func = None
        self.run_args = ((), {})
        self.called = False

    def get_request_queue(self, node):
        if not self.request_queue:
            queue_group = node.queue_group
            self.request_queue = get_request_queue(self.cs_manager, queue_group)
            self.request_queue.add(self)
        return self.request_queue

    def __getattr__(self, item):
        if hasattr(self.node_cls, item):
            self.run_func = item
            return self.__call__
        return self.__getattribute__(item)

    def unset(self):
        super().unset()
        self.node = None
        self.request_queue = None

    def __call__(self, *args, **kwargs):
        self.unset()
        self.run_args = (args, kwargs)
        self.called = True

        log.request.info(
            f"Starting request {self} {self.cs_manager} {self.node_id} {self.node_cls} {self.run_args}"
        )

        if not protocol.isDispatchThread():
            protocol.invokeLater(self._invoke)
        else:
            self._invoke()
        return self

    def _invoke(self):
        if not self.cs_manager.is_ready:
            log.request.debug(f"cs_manager not ready {self}")
            protocol.invokeLaterWithDelay(1, self._invoke)
            return

        node = self.cs_manager.get_node(self.node_id)

        if not node:
            self.set_exception(Exception(f"Could not find context for {self.node_id}"))
            return

        request_queue = self.get_request_queue(node)

        if not request_queue.is_first(self):
            log.request.info(f"Queuing {self} {node.queue_group}")
            return

        if not node.is_ready:
            log.request.debug(f"Node not ready {self}")
            protocol.invokeLaterWithDelay(1, self._invoke)
            return

        try:
            node = self.cs_manager.get_node(self.node_id, self.node_cls)
        except Exception as e:
            self.set_exception(e)
            return

        if not node:
            self.set_exception(
                Exception(f"Could not find context for {self.node_id} of type {self.node_cls}")
            )
            return

        if not node.is_ready:
            log.request.debug(f"Node class switch not ready {self}")
            protocol.invokeLaterWithDelay(1, self._invoke)
            return

        self.node = node
        args, kwargs = self.run_args
        try:
            log.request.info(f"Running {self} {self.run}")
            node.request = self
            result = self.run(*args, **kwargs)
            if result is not None:
                self._result = result
        except Exception as e:
            # exception_type = type(e).__name__
            # exception_message = e
            # self.error = f"({exception_type}) {exception_message}"
            self._error = e

        if self.called and self._result is not None or self._error:
            self.done_run(self, self._error, self._result)

    def run(self, *args, **kwargs):
        if isinstance(self.run_func, str):
            self.run_func = getattr(self.node, self.run_func)
        done = kwargs.get("done")
        sig = inspect.signature(self.run_func)
        has_done = "done" in sig.parameters.keys()
        if has_done and not done and args and len(sig.parameters) == len(args):
            done = args[-1]
            args = args[:-1]
        if done:
            self._done_callback = CsFuture._wrap_callback(done)

        if has_done:
            kwargs["done"] = self.done_run
        elif done:
            del kwargs["done"]

        # NOTE - Only if the progress_update var has a valid CsRequestProgressUpdate instance obj
        #  as its value, add this to the kwargs. Many existing funcs dont expect to get the
        #  "progress_update" argument and error out.
        if "progress_update" in sig.parameters.keys():
            kwargs["progress_update"] = self.progress_update

        result = None
        if self.run_func:
            log.request.debug(f"Run func {self.run_func} ({args}, {kwargs}")
            result = self.run_func(*args, **kwargs)
            if not self.node.is_ready:
                result = None
        else:
            self._error = Exception("No run function set for request")
        return result

    def _invoke_done(self):
        log.request.info(f"Done Run {self}")
        super()._invoke_done()
        self.node.request = None
        self.run_func = None
        self.node.remove_pending(self)
        if self.request_queue:
            self.request_queue.done_request(self)
        self.called = False

    def done_run(self, token=None, error=None, result=None):
        self._error = error
        self._result = result
        self._invoke_done()

    def progress_update(self, token=None, error=None, result=None):
        if not self._error:
            self._error = error
        self.set_progress(result)

    def default_run_func(self, done=None, progress_update=None):
        self._result = self.cs_manager[self.node_id]


class CsFutureRequestSync(CsFutureRequest):
    def __init__(
        self,
        cs_manager: CsManager,
        node_id: str = "",
        node_cls: Type[Node] = Node,
        timeout: int = None,
        *args,
        **kwargs,
    ):
        super(CsFutureRequestSync, self).__init__(cs_manager, node_id, node_cls, *args, **kwargs)
        self.cond = threading.Event()
        self.timeout = timeout

    def _invoke_done(self):
        super()._invoke_done()
        self.cond.set()

    def wait(self, timeout: int = None):
        if protocol.isDispatchThread():
            return
        if timeout is not None:
            self.timeout = timeout
        completed = self.cond.wait(self.timeout)
        log.request.debug(
            f"Request sync done {self._error} {self._result} completed {completed} {self}"
        )
        if not completed and not self._error:
            self.cancel()
            raise Exception("Request timed out.")
        else:
            self._finalize()

    @property
    def result(self):
        self.wait()
        return super().result

    @property
    def error(self):
        self.wait()
        return super().error

    def __call__(self, *args, **kwargs):
        self.cond.clear()

        if "timeout" in kwargs:
            self.timeout = kwargs.pop("timeout")

        # if done is set then don't wait
        should_wait = True
        if self._done_callback or "done" in kwargs:
            should_wait = False
        elif self.run_func:
            run_func = self.run_func
            if isinstance(run_func, str):
                run_func = getattr(self.node_cls, run_func)
            if run_func:
                sig = inspect.signature(run_func)
                done_index = None
                for i, k in enumerate(sig.parameters.keys()):
                    if k == "done":
                        done_index = i
                        break
                if done_index is not None and len(args) > done_index:
                    should_wait = False

        log.request.info(f"Request sync start {self} timeout {self.timeout}")

        super(CsFutureRequestSync, self).__call__(*args, **kwargs)

        if not should_wait:
            return self

        return self.result
