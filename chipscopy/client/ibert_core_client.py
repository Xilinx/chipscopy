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

from typing import Union, List, Dict

from chipscopy import dm
from chipscopy.client import core
from chipscopy.client.core import CoreClient
from chipscopy.dm.request import DoneCallback
from chipscopy.utils import listify
from chipscopy.utils.logger import log

DOMAIN_NAME = "client_ibert"


class IBERTCoreClient(CoreClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return_val = node.type and node.type == "ibert"
        return return_val

    def post_init(self):
        super(IBERTCoreClient, self).post_init()

    def get_child_with_name(self, name: str, done: DoneCallback):
        """
        Iterate through the children of this IBERT and return Node with matching name.
        """
        for child_ctx in self.children:
            child_node = self.manager.get_node(child_ctx)
            # Only nodes that are safe to read from will have the 'display_name' prop set.
            # eg: If the access path check returns False for certain child_nodes of GTYP,
            # their 'display_name' prop won't be set.
            if "display_name" in child_node.props and name == child_node.props["display_name"]:
                done(result=child_node)
                return

        done()

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService("IBERT")

    def initialize(self, done: DoneCallback = None):
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initializing IBERT service")
        token = service.initialize(self.ctx, done_cb)
        return self.add_pending(token)

    def setup(self, done: DoneCallback = None):
        service, done_cb = self.make_done(done)
        options = {"node_id": self.ctx}
        token = service.setup(options, done_cb)
        return self.add_pending(token)

    def read(
        self,
        start_address: int,
        endpoint_display_name: str,
        size: int = 1,
        *,
        done: DoneCallback = None,
    ):
        """
        Command to do single or burst read.

        Args:
            start_address (int): The address to read from.

            endpoint_display_name (str): Display name for the endpoint the register is located in.

            size (int): **(Optional)** The number of words to read. Default = 1.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            str:
                Format - `"{Address as hex} : {Value in hex} : {Value as bin}"`

        Usage
            ::

                #
                >>> ibert.read(0x3000, "Quad_0")
                0x3000 : 0x0000_1234 : 0b0000_0000_0000_0000_0001_0010_0011_0100
                >>> ibert.read(0x3000, "Quad_0", 5)
                0x3000 : 0x0000_1234 : 0b0000_0000_0000_0000_0001_0010_0011_0100
                0x3004 : 0x0000_0000 : 0b0000_0000_0000_0000_0000_0000_0000_0000
                0x3008 : 0x0870_0000 : 0b0000_1000_0111_0000_0000_0000_0000_0000
                0x300C : 0x0000_0000 : 0b0000_0000_0000_0000_0000_0000_0000_0000
                0x3010 : 0x0000_0000 : 0b0000_0000_0000_0000_0000_0000_0000_0000

        """
        service, done_cb = self.make_done(done)
        options = {
            "node_id": self.ctx,
            "endpoint_name": endpoint_display_name,
            "start": start_address,
            "size": size,
        }
        token = service.read(options, done_cb)
        return self.add_pending(token)

    def write(
        self,
        start_address: int,
        data: int,
        endpoint_display_name: str,
        *,
        done: DoneCallback = None,
    ):
        """
        Command to write a value to an address.

        Args:
            start_address (int): Address to write to.

            data (int): Value to write.

            endpoint_display_name (str): Display name for the endpoint the register is located in.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            None

        Usage
            ::

                #
                >>> ibert.write(0x1234, 0xABCD_EF12, "Quad_0")
                None

        """
        service, done_cb = self.make_done(done)
        options = {
            "node_id": self.ctx,
            "endpoint_name": endpoint_display_name,
            "start": start_address,
            "data": data,
        }
        token = service.write(options, done_cb)
        return self.add_pending(token)

    def get_layout(self, *, done: DoneCallback = None):
        """
        Get the hierarchy of objects in the IBERT node and the properties associated at each level.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict: Nested dictionaries with 2 keys at every level - "Properties" and "Children".

        """
        service, done_cb = self.make_done(done)
        options = {"node_id": self.ctx}
        token = service.get_layout(options, done_cb)
        return self.add_pending(token)

    def get_property(
        self,
        property_names: Union[str, List[str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        """
        Get value of the properties from the core object.

        Args:
            property_names (str or list[str]): A string with the name of the property OR
                a list of property name string(s).

            endpoint_name (str): Display name of the endpoint to which the
                property(properties) belong.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, str) or str: String or dictionary depending on how the command is invoked.
            See below for examples.

        Usage
            ::

                # String as first argument
                >>> ibert.get_property("<Property name>", "Quad_0")
                "<Property value">

                # List of length 1 as first argument
                >>> ibert.get_property(["<Property name>"], "Quad_0")
                "<Property value">

                # List of length 3 as first argument
                >>> ibert.get_property(
                >>>     [
                >>>         "<Property 1 name>",
                >>>         "<Property 1 name>",
                >>>         "<Property n name>",
                >>>     ],
                >>>     "Quad_0"
                >>> )
                {
                    "<Property 1 name>": "<Property value>",
                    "<Property 2 name>": "<Property value>",
                    "<Property n name>": "<Property value>",
                }

        """
        service, done_cb = self.make_done(done)
        if isinstance(property_names, str):
            property_names = [property_names]
        options = {
            "node_id": self.ctx,
            "Property Names": property_names,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.get_property(options, done_cb)
        return self.add_pending(token)

    def get_property_group(self, groups: Union[str, List[str]], *, done: DoneCallback = None):
        """
        Get value of the properties in property group(s) from the core object.

        Args:
            groups (list[str] or str):  A string with the name of the property group OR
                a list of property group string(s).

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict: Dictionary with depth of 1 or 2, depending on how the command is invoked.
            See below for examples

        Usage
            ::

                # String as argument
                >>> ibert.get_property_group("<Property group name>")
                {
                    "<Property 1 name>": "<Property value>",
                    "<Property 2 name>": "<Property value>",
                    "<Property n name>": "<Property value>",
                }

                # List of length 1 as argument
                >>> ibert.get_property_group(["<Property group name>"])
                {
                    "<Property 1 name>": "<Property value>",
                    "<Property 2 name>": "<Property value>",
                    "<Property n name>": "<Property value>",
                }

                # List of length 3 as argument
                >>> ibert.get_property_group(
                >>>    [
                >>>         "<Property group 1 name>",
                >>>         "<Property group 2 name>",
                >>>         "<Property group n name>"
                >>>    ]
                >>> )
                {
                    "<Property group 1 name>":  {
                        "<Property 1 name>": "<Property value>",
                        "<Property 2 name>": "<Property value>",
                        "<Property n name>": "<Property value>",
                    },
                    "<Property group 2 name>": {
                        "<Property 1 name>": "<Property value>",
                        "<Property 2 name>": "<Property value>",
                        "<Property n name>": "<Property value>",
                    },
                    "<Property group n name>": {
                        "<Property 1 name>": "<Property value>",
                        "<Property 2 name>": "<Property value>",
                        "<Property n name>": "<Property value>",
                    }
                }

        """
        service, done_cb = self.make_done(done)
        if isinstance(groups, str):
            groups = [groups]
        options = {"node_id": self.ctx, "Groups": groups}
        token = service.get_property_group(options, done_cb)
        return self.add_pending(token)

    def set_property(
        self,
        property_dict: Dict[str, Union[int, str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        """
        Set a new value for the property in the core object.

        Args:
            property_dict (dict): A dictionary with key, value pair as the property name and
                new value for property.

            endpoint_name (str): Display name of the endpoint to which the
                property(properties) belong.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            None

        Usage
            ::

                #
                >>> ibert.set_property(
                >>>     {
                >>>         "<Property 1>": "<New value>",
                >>>         "<Property 2>": "<New value>",
                >>>         "<Property n>": "<New value>",
                >>>     },
                >>>     "Quad_0"
                >>> )
                None

        """
        service, done_cb = self.make_done(done)
        options = {
            "node_id": self.ctx,
            "Property Dict": property_dict,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.set_property(options, done_cb)
        return self.add_pending(token)

    def refresh_property(
        self,
        property_names: Union[str, List[str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        """
        Update value of properties from the core.

        Args:
            property_names (str or list(str)): A string with the name of the property OR a list
                of property name string(s).

            endpoint_name (str): Display name of the endpoint to which the
                property(properties) belong.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, str) or str: String or dictionary depending on how the command is invoked.
            See below for examples.

        Usage
            ::

                # String as first argument
                >>> ibert.refresh_property("<Property name>", "Quad_0")
                "<Refreshed value>"

                # List of length 1 as first argument
                >>> ibert.refresh_property(["<Property name>"], "Quad_0")
                "<Refreshed value>"

                # List of length 3 as first argument
                >>> ibert.refresh_property(
                >>>     [
                >>>         "<Property 1 name>",
                >>>         "<Property 2 name>",
                >>>         "<Property n name>"
                >>>     ],
                >>>     "Quad_0"
                >>> )
                {
                    "<Property 1 name>": "<Refreshed value>",
                    "<Property 2 name>": "<Refreshed value>",
                    .
                    .
                    .
                    "<Property n name>": "<Refreshed value>",
                }

        """
        service, done_cb = self.make_done(done)
        if isinstance(property_names, str):
            property_names = [property_names]
        options = {
            "node_id": self.ctx,
            "Property Names": property_names,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.refresh_property(options, done_cb)
        return self.add_pending(token)

    def refresh_property_group(self, groups: Union[str, List[str]], *, done: DoneCallback = None):
        """
        Update the value of the properties in the property group(s) by reading from the core.

        Args:
            groups (str or list[str]): The group name to refresh as a string OR a list of group
                name as string(s).

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict - Dictionary with a depth of 1 or 2, depending on how the command is invoked.
            See below for examples.

        Usage
            ::

                # String as argument
                >>> ibert.refresh_property_group("<Property group name>")
                {
                    "<Property 1 name>": "<Refreshed value>",
                    "<Property 2 name>": "<Refreshed value>",
                    "<Property n name>": "<Refreshed value>",
                }

                # List of length 1 as argument
                >>> ibert.refresh_property_group(["<Property group name>"])
                {
                    "<Property 1 name>": "<Refreshed value>",
                    "<Property 2 name>": "<Refreshed value>",
                    "<Property n name>": "<Refreshed value>",
                }

                # List of length 3 as argument
                >>> ibert.refresh_property_group(
                >>>    [
                >>>         "<Property group 1 name>",
                >>>         "<Property group 2 name>",
                >>>         "<Property group n name>"
                >>>    ]
                >>> )
                {
                    "<Property group 1 name>": {
                        "<Property 1 name>": "<Refreshed value>",
                        "<Property 2 name>": "<Refreshed value>",
                        "<Property n name>": "<Refreshed value>",
                    },
                    "<Property group 2 name>": {
                        "<Property 1 name>": "<Refreshed value>",
                        "<Property 2 name>": "<Refreshed value>",
                        "<Property n name>": "<Refreshed value>",
                    },
                    "<Property group n name>": {
                        "<Property 1 name>": "<Refreshed value>",
                        "<Property 2 name>": "<Refreshed value>",
                        "<Property n name>": "<Refreshed value>",
                    }
                }

        """
        service, done_cb = self.make_done(done)
        if isinstance(groups, str):
            groups = [groups]
        options = {"node_id": self.ctx, "Groups": groups}
        token = service.refresh_property_group(options, done_cb)
        return self.add_pending(token)

    def commit_property(
        self,
        property_names: Union[str, List[str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        """
        Commit the current value of the properties in the object to the core.

        Args:
            property_names (str or list[str]): The property name to commit as a string OR a list
                of property name string(s).

            endpoint_name (str): Display name of the endpoint to which the
                property(properties) belong.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            None

        Usage
            ::

                #
                >>> ibert.commit_property("<Property name>", "Quad_0")
                None

                >>> ibert.commit_property(
                >>>     [
                >>>         "<Property 1 name">,
                >>>         "<Property 2 name">,
                >>>         "<Property n name">,
                >>>     ],
                >>>     "Quad_0"
                >>> )
                None

        """
        service, done_cb = self.make_done(done)
        if isinstance(property_names, str):
            property_names = [property_names]
        options = {
            "node_id": self.ctx,
            "Property Names": property_names,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.commit_property(options, done_cb)
        return self.add_pending(token)

    def list_property_groups(self, *, done: DoneCallback = None):
        """
        Lists the available property groups.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            list(str): A list of group names

        Usage
            ::

                #
                >>> ibert.list_property_groups
                ["<Property group 1 name>", "<Property group 2 name>", "<Property group n name>"]

        """
        service, done_cb = self.make_done(done)
        options = {"node_id": self.ctx}
        token = service.list_property_groups(options, done_cb)
        return self.add_pending(token)

    def add_to_property_watchlist(
        self,
        property_names: Union[str, List[str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        service, done_cb = self.make_done(done)
        property_names = listify(property_names)
        options = {
            "node_id": self.ctx,
            "Property Names": property_names,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.add_to_property_watchlist(options, done_cb)
        return self.add_pending(token)

    def remove_from_property_watchlist(
        self,
        property_names: Union[str, List[str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        service, done_cb = self.make_done(done)
        property_names = listify(property_names)
        options = {
            "node_id": self.ctx,
            "Property Names": property_names,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.remove_from_property_watchlist(options, done_cb)
        return self.add_pending(token)

    def report_property(
        self,
        property_names: Union[str, List[str]],
        endpoint_name: str,
        *,
        done: DoneCallback = None,
    ):
        """
        Get detailed report about a property/properties.

        Args:
            property_names (str or list(str)): The name of the property to get report for a list
                of property name string(s).

            endpoint_name (str): Display name of the endpoint to which the
                property(properties) belong.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict: The report for a property may vary based on the type of properties

        Usage
            ::

                # Report property on a regular property
                >>> ibert.report_property("Property A", "Quad_0")
                {
                    "Property A": {
                        "Name": "Property A",
                        "Description: "This is a regular property, that can have any value",
                        "Permission": [
                            "GET",
                            "SET",
                            "COMMIT",
                            "REFRESH"
                        ],
                        "Default value": "0",
                        "Groups": [
                            "Group 1",
                            "Group 2"
                        ],
                        "Current value": "23",
                        "Value type": str
                    }
                }

                # Property B is an enumerated property
                # In this case, an additional key "Valid values" is included in the report
                >>> ibert.report_property("Property B", "Quad_0")
                {
                    "Property B":  {
                        "Name": "Property B",
                        "Description: "This is an enumerated property",
                        "Permission": [
                            "GET",
                            "SET",
                            "COMMIT",
                            "REFRESH"
                        ],
                        "Default value": "0",
                        "Groups": [
                            "Group 1",
                            "Group 2"
                        ],
                        "Current value": "23",
                        "Valid values": [
                            "0",
                            "10",
                            "14",
                            "23",
                            "50"
                        ],
                        "Value type": str
                    }
                }

        """
        service, done_cb = self.make_done(done)
        if isinstance(property_names, str):
            property_names = [property_names]
        options = {
            "node_id": self.ctx,
            "Property Names": property_names,
            "Endpoint Display Name": endpoint_name,
        }
        token = service.report_property(options, done_cb)
        return self.add_pending(token)

    def start_eye_scan(
        self,
        rx_name: str,
        scan_parameters=None,
        *,
        done: DoneCallback = None,
    ):
        service, done_cb = self.make_done(done)

        if scan_parameters is None:
            scan_parameters = dict()

        options = {"node_id": self.ctx, "RX Name": rx_name, "Scan Parameters": scan_parameters}

        token = service.start_eye_scan(options, done_cb)
        return self.add_pending(token)

    def terminate_eye_scan(self, rx_name: str, *, done: DoneCallback = None):
        service, done_cb = self.make_done(done)

        options = {"node_id": self.ctx, "RX Name": rx_name}

        token = service.terminate_eye_scan(options, done_cb)
        return self.add_pending(token)

    def get_eye_scan_parameters(self, rx_name: str = None, *, done: DoneCallback = None):
        service, done_cb = self.make_done(done)

        if rx_name is None:
            rx_name = list()

        if isinstance(rx_name, str):
            rx_name = [rx_name]

        options = {"node_id": self.ctx, "RX Name": rx_name}
        token = service.get_eye_scan_parameters(options, done_cb)
        return self.add_pending(token)

    def start_yk_scan(self, rx_name: str, *, done: DoneCallback = None):
        service, done_cb = self.make_done(done)

        options = {"node_id": self.ctx, "RX Name": rx_name}

        token = service.start_yk_scan(options, done_cb)
        return self.add_pending(token)

    def terminate_yk_scan(self, rx_name: str, *, done: DoneCallback = None):
        service, done_cb = self.make_done(done)

        options = {"node_id": self.ctx, "RX Name": rx_name}

        token = service.terminate_yk_scan(options, done_cb)
        return self.add_pending(token)
