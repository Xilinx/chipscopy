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

from collections.abc import Sequence
from typing import Tuple
from chipscopy import dm
from chipscopy.dm import request
from chipscopy.tcf import services
from chipscopy.tcf.services import local, from_xargs


class CsRequestDone(request.DoneRequest):
    def __init__(self, req, service_name: str, name: str = ""):
        self._name = name

        self.req = req
        self.service_name = service_name

    def done_request(self, token, error, args):
        if error:
            e_msg = f"ChipScope Service {self.service_name} {self._name}: {error}"
            self.req.sendError(e_msg)
        else:
            self.req.sendXicomResult(args)


class CsRequestProgressUpdate(request.ProgressRequest):
    def __init__(self, req, service_name: str, name: str = ""):
        self._name = name

        self.req = req
        self.service_name = service_name

    def done_progress(self, token, error, result):
        self.req.sendXicomProgress(result)


class DefaultCoreService(services.Service):
    """Abstract class for property based debug cores including harden blocks."""

    def getName(self):
        raise NotImplementedError("Abstract method")

    def __init__(self, cls_type: type, progress_update_supported: bool = False):
        super().__init__(None)
        self._class_type = cls_type
        self._progress_update_supported: bool = progress_update_supported

    def _get_args(
        self, req: local.CommandRequest, in_arg_count: int, function_name: str = ""
    ) -> Tuple:
        args = from_xargs(req.args)
        if len(args) < in_arg_count:
            raise Exception(
                f"Insufficient arguments. Need {in_arg_count} argument(s),"
                f" but given only {len(args)} argument(s)."
            )
        csm_name, node = dm.parse_node_id(args[0])
        cs_manager = dm.get_manager(csm_name)
        cs_req = request.CsRequest(
            cs_manager,
            node,
            self._class_type,
            CsRequestDone(req, self.getName(), function_name),
            # Note - Only if the core supports progress_update callbacks create
            #  a CsRequestProgressUpdate object. The "run" func in request.py makes use of
            #  this to decide whether or not to pass this argument to the function being called
            CsRequestProgressUpdate(req, self.getName(), function_name)
            if self._progress_update_supported
            else None,
        )
        return (cs_req, *args[1:])

    def _require_dict(self, req: local.CommandRequest, arg_index: int) -> None:
        if len(req.args) < arg_index + 1 or not isinstance(req.args[arg_index], dict):
            raise ValueError(
                f"Expected argument in position {arg_index + 1} to be a dict or a map."
            )
        return

    def _require_seq(self, req: local.CommandRequest, arg_index: int) -> None:
        if len(req.args) < arg_index + 1 or not isinstance(
            req.args[arg_index], Sequence
        ):
            raise ValueError(
                f"Expected argument in position {arg_index + 1} to be a list."
            )
        return

    def _require_dict_dict(self, req: local.CommandRequest, arg_index: int) -> None:
        self._require_dict(req, arg_index)
        for dd in req.args[arg_index].values():
            if not isinstance(dd, dict):
                raise ValueError(
                    f"Expected argument in position {arg_index + 1} to be a dict-of-dicts or a map-of-maps."
                )
        return

    def _require_seq_dict(self, req: local.CommandRequest, arg_index: int) -> None:
        self._require_seq(req, arg_index)
        for dd in req.args[arg_index]:
            if not isinstance(dd, dict):
                raise ValueError(
                    f"Expected argument in position {arg_index + 1} to be a list-of-dicts."
                )
        return

    def getPropertyCmd(self, req: local.CommandRequest):
        cs_req, property_names = self._get_args(req, 2, "get_property")
        cs_req.get_property(property_names)

    def getPropertyGroupCmd(self, req: local.CommandRequest):
        cs_req, property_group_names = self._get_args(req, 2, "get_property_group")
        cs_req.get_property_group(property_group_names)

    def reportPropertyCmd(self, req: local.CommandRequest):
        cs_req, property_names = self._get_args(req, 2, "report_property")
        cs_req.report_property(property_names)

    def reportPropertyGroupCmd(self, req: local.CommandRequest):
        cs_req, property_group_names = self._get_args(req, 2, "report_property_group")
        cs_req.report_property_group(property_group_names)

    def resetPropertyCmd(self, req: local.CommandRequest):
        cs_req, property_names = self._get_args(req, 2, "reset_property")
        cs_req.reset_property(property_names)

    def resetPropertyGroupCmd(self, req: local.CommandRequest):
        cs_req, property_group_names = self._get_args(req, 2, "reset_property_group")
        cs_req.reset_property_group(property_group_names)

    def setPropertyCmd(self, req: local.CommandRequest):
        cs_req, property_values = self._get_args(req, 2, "set_property")
        self._require_dict(req, 1)
        cs_req.set_property(property_values)

    def setPropertyGroupCmd(self, req: local.CommandRequest):
        cs_req, property_values = self._get_args(req, 2, "set_property_group")
        self._require_dict(req, 1)
        cs_req.set_property_group(property_values)

    def listPropertyGroupsCmd(self, req: local.CommandRequest):
        (cs_req,) = self._get_args(req, 1, "list_property_groups")
        cs_req.list_property_groups()

    def commitPropertyGroupCmd(self, req: local.CommandRequest):
        cs_req, property_group_names = self._get_args(req, 2, "commit_property_group")
        cs_req.commit_property_group(property_group_names)

    def refreshPropertyGroupCmd(self, req: local.CommandRequest):
        cs_req, groups = self._get_args(req, 2, "refresh_property_group")
        cs_req.refresh_property_group(groups)

    def add_to_property_watchlist_cmd(self, req: local.CommandRequest):
        cs_req, options = self._get_args(req, 2, "add_to_property_watchlist")
        cs_req.add_to_watchlist(options)

    def remove_from_property_watchlist_cmd(self, req: local.CommandRequest):
        cs_req, options = self._get_args(req, 2, "remove_from_property_watchlist")
        cs_req.remove_from_watchlist(options)

    # For testing
    def commitMemoryCmd(self, req: local.CommandRequest):
        (cs_req, property_name, buffer, start_byte_index, word_byte_length) = self._get_args(req, 5, "commit_memory")
        return cs_req.commit_memory(property_name, buffer, start_byte_index, word_byte_length)

    # For testing
    def refreshMemoryCmd(self, req: local.CommandRequest):
        (cs_req, property_name, word_count, start_byte_index, word_byte_length) = \
            self._get_args(req, 5, "refresh_memory")
        return cs_req.refresh_memory(property_name, word_count, start_byte_index, word_byte_length)
