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

from chipscopy.tcf.services import ServiceProvider, add_service_provider
from chipscopy.utils.logger import log


class ProxiesServiceProvider(ServiceProvider):
    package_base = str(__package__)

    def get_local_service(self, channel):
        return ()

    def get_service_proxy(self, channel, service_name: str):
        package_base = str(__package__)
        service = None
        try:
            clsName = service_name + "Proxy"
            package = package_base + "." + clsName
            clsModule = __import__(package, fromlist=[clsName], globals=globals())
            cls = clsModule.__dict__.get(clsName)
            service = cls(channel)
        except ImportError:
            pass
        except Exception as x:
            log.all.error(f"Cannot instantiate service proxy for {service_name}: {x}")
        return service


def init():
    add_service_provider(ProxiesServiceProvider())
