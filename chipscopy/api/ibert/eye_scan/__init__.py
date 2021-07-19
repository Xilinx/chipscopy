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

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Event
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple

from rich.box import SQUARE as BOX_SQUARE
from rich.table import Table

from chipscopy.api.ibert.aliases import (
    EYE_SCAN_2D_PLOT,
    EYE_SCAN_2D_PLOT_BER_FLOOR_VALUE,
    EYE_SCAN_2D_PLOT_DATA,
    EYE_SCAN_ABORTED,
    EYE_SCAN_DONE,
    EYE_SCAN_ERROR_COUNT,
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_IN_PROGRESS,
    EYE_SCAN_NOT_STARTED,
    EYE_SCAN_PRESCALE,
    EYE_SCAN_PROGRESS,
    EYE_SCAN_RAW_DATA,
    EYE_SCAN_SAMPLE_COUNT,
    EYE_SCAN_SCAN_PARAMETERS,
    EYE_SCAN_START_TIME,
    EYE_SCAN_STATUS,
    EYE_SCAN_STOP_TIME,
    EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_EXPECTED,
    EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_READ,
    EYE_SCAN_UT,
    EYE_SCAN_VERT_RANGE,
    MB_ELF_VERSION,
)
from chipscopy.api.ibert.rx import RX
from chipscopy.api.ibert.eye_scan.params import EyeScanParam
from chipscopy.api.ibert.eye_scan.plotter import EyeScanPlot
from chipscopy.utils.printer import printer, PercentProgressBar


if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.dm import Node

common_progress = PercentProgressBar()


@dataclass
class ScanPoint:
    x: int
    y: int
    ber: float
    errors: int
    samples: int


@dataclass(frozen=True)
class Plot2DData:
    scan_points: Dict[Tuple[int, int], ScanPoint]
    """Collection of :py:class:`ScanPoint` instances to represent the 2D eye scan plot"""

    ber_floor_value: float
    """This value is used as the ``ber`` value for any X, Y coordinate whose computed BER was 0"""


@dataclass
class RawData:
    """
    Class for storing raw data from the MicroBlaze. The size of all the lists in this class
    will be the same
    """

    ut: List[int]
    prescale: List[int]
    error_count: List[int]
    sample_count: List[int]
    vertical_range: List[int]
    horizontal_range: List[int]


@dataclass
class ScanData:
    """
    Class for storing raw scan data and 2D plot data
    """

    raw: RawData
    """Raw scan data from the MicroBlaze"""

    all_params: dict
    """All parameters the server used to run the scan in the MicroBlaze"""

    processed: Plot2DData = None
    """2D plot data. This will only be available if the scan completed successfully"""


@dataclass
class EyeScan:
    """
    Class for interacting with eye scans.
    **Please do not** create an instance of this class directly. Please use the factory method
    :py:func:`~chipscopy.api.ibert.create_eye_scans` instead.
    """

    rx: RX
    """:py:class:`RX` object attached to this eye scan"""

    name: str
    """Name of the eye scan"""

    params: Dict[str, EyeScanParam] = field(default_factory=dict)
    """Dictionary containing the py:class:`EyeScanParam` instance for every available param"""

    done_callback: Callable[["EyeScan"], None] = None
    """Callback function called when eye scan has ended"""

    progress_callback: Callable[[float], None] = None
    """Callback function called when eye scan update is received"""

    filter_by: Dict[str, Any] = field(default_factory=dict)

    status: str = EYE_SCAN_NOT_STARTED
    """Status of the eye scan"""

    progress: float = -1.0
    """Progress of the eye scan in %"""

    stop_time: datetime = None
    """Time stamp of when eye scan was stopped in cs_server"""

    start_time: datetime = None
    """Time stamp of when eye scan was started in cs_server"""

    elf_version: str = None
    """ELF version read from the MicroBlaze"""

    data_points_read: int = -1
    """Number of data points scanned by the MicroBlaze"""

    data_points_expected: int = -1
    """Total number of data points expected to be scanned by the MicroBlaze"""

    scan_data: ScanData = None
    """Scan data stored in an instance of the :py:class:`ScanData` class"""

    plot: EyeScanPlot = None
    """`EyeScanPlot` instance for interacting with the plot"""

    _handle_from_cs_server: Optional[str] = None

    _task_id = None

    _scan_done_event: Event = field(default_factory=Event)

    def __repr__(self) -> str:
        return self.name

    def __post_init__(self):
        self.rx.eye_scan = self
        self.rx.eye_scan_names.append(self.name)

        self.filter_by = {"rx": self.rx, "name": self.name}

        if self.rx.link is not None:
            self.filter_by["link"] = self.rx.link

        all_params = self.rx.core_tcf_node.get_eye_scan_parameters(rx_name=self.rx.handle)
        valid_values = all_params["Valid Values"]
        default_values = all_params["Default Value"]
        for param in all_params["Parameter Names"]:
            self.params[param] = EyeScanParam(param)
            if param in valid_values:
                self.params[param].modifiable = True
                self.params[param].valid_values = valid_values[param]
                self.params[param].default_value = default_values[param]

        # Todo - Remove event listener after done with everything
        self.rx.property.endpoint_tcf_node.add_listener(self._scan_update_event_listener)

    def _clear_out_old_data(self):
        self.status = EYE_SCAN_NOT_STARTED
        self.progress = -1.0
        self.stop_time = None
        self.start_time = None
        self.elf_version = None
        self.scan_data = None
        self.data_points_read = -1
        self.data_points_expected = -1

        self._scan_done_event.clear()

    def _get_status(self) -> str:
        if self.status == EYE_SCAN_IN_PROGRESS:
            return PercentProgressBar.Status.IN_PROGRESS.value
        elif self.status == EYE_SCAN_ABORTED:
            return PercentProgressBar.Status.ABORTED.value
        elif self.status == EYE_SCAN_DONE:
            return PercentProgressBar.Status.DONE.value
        else:
            return f"[bold]{self.status}[/]"

    def invalidate(self):
        self.rx.eye_scan = None
        self.rx.eye_scan_names.remove(self.name)

        self.rx = None
        self.name = ""
        self._clear_out_old_data()

    def start(self, *, show_progress_bar: bool = True):
        """
        Send command to cs_server to start the eye scan in the HW.

        Args:
            show_progress_bar: Set to true to show progress bar on stdout

        """
        self._clear_out_old_data()

        scan_params = dict()
        for param in self.params.values():
            if param.value is not None:
                if not param.modifiable:
                    printer(
                        f"Scan parameter '{param.name} is not modifiable! It will be ignored",
                        level="warning",
                    )
                    continue
                scan_params[param.name] = param.value

        self._handle_from_cs_server = self.rx.core_tcf_node.start_eye_scan(
            rx_name=self.rx.handle,
            scan_parameters=scan_params,
        )

        self._task_id = common_progress.add_task(
            description=f"{self.name} progress ",
            status=self._get_status(),
            visible=show_progress_bar,
        )

    def _scan_update_event_listener(self, node: "Node", updated_properties: Set[str]):
        # NOTE - This is called on the TCF event dispatcher thread
        if len(updated_properties) == 0:
            return

        try:
            # TODO - Merge this condition with the one at the top
            if self._handle_from_cs_server not in updated_properties:
                return

            scan_report = node.props[self._handle_from_cs_server]

            # Not expected to change after scan start
            if self.start_time is None and EYE_SCAN_START_TIME in scan_report:
                self.start_time = datetime.strptime(
                    scan_report[EYE_SCAN_START_TIME], "%Y-%m-%d %H:%M:%S.%f"
                )

            # Not expected to change after scan stop
            if self.stop_time is None and EYE_SCAN_STOP_TIME in scan_report:
                self.stop_time = datetime.strptime(
                    scan_report[EYE_SCAN_STOP_TIME], "%Y-%m-%d %H:%M:%S.%f"
                )

            # Not expected to change after scan start
            if self.elf_version is None and MB_ELF_VERSION in scan_report:
                self.elf_version = scan_report[MB_ELF_VERSION]

            # Not expected to change after scan start
            if (
                self.data_points_expected == -1
                and EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_EXPECTED in scan_report
            ):
                self.data_points_expected = int(
                    scan_report[EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_EXPECTED]
                )

            if EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_READ in scan_report:
                self.data_points_read = int(scan_report[EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_READ])

            if EYE_SCAN_SCAN_PARAMETERS in scan_report and EYE_SCAN_RAW_DATA in scan_report:
                new_ut = scan_report[EYE_SCAN_RAW_DATA][EYE_SCAN_UT]
                new_prescale = scan_report[EYE_SCAN_RAW_DATA][EYE_SCAN_PRESCALE]
                new_error_count = scan_report[EYE_SCAN_RAW_DATA][EYE_SCAN_ERROR_COUNT]
                new_sample_count = scan_report[EYE_SCAN_RAW_DATA][EYE_SCAN_SAMPLE_COUNT]
                new_vertical_range = scan_report[EYE_SCAN_RAW_DATA][EYE_SCAN_VERT_RANGE]
                new_horizontal_range = scan_report[EYE_SCAN_RAW_DATA][EYE_SCAN_HORZ_RANGE]

                if self.scan_data is None:
                    self.scan_data = ScanData(
                        raw=RawData(
                            ut=new_ut,
                            prescale=new_prescale,
                            error_count=new_error_count,
                            sample_count=new_sample_count,
                            vertical_range=new_vertical_range,
                            horizontal_range=new_horizontal_range,
                        ),
                        all_params=scan_report[EYE_SCAN_SCAN_PARAMETERS],
                    )

                else:
                    self.scan_data.raw.ut.extend(new_ut)
                    self.scan_data.raw.prescale.extend(new_prescale)
                    self.scan_data.raw.error_count.extend(new_error_count)
                    self.scan_data.raw.sample_count.extend(new_sample_count)
                    self.scan_data.raw.vertical_range.extend(new_vertical_range)
                    self.scan_data.raw.horizontal_range.extend(new_horizontal_range)

            if EYE_SCAN_2D_PLOT in scan_report:
                ber_floor_value = scan_report[EYE_SCAN_2D_PLOT][EYE_SCAN_2D_PLOT_BER_FLOOR_VALUE]

                scan_points: Dict[Tuple[int, int], ScanPoint] = dict()
                for key, data in scan_report[EYE_SCAN_2D_PLOT][EYE_SCAN_2D_PLOT_DATA].items():
                    x, y = [int(coordinate) for coordinate in key.split(", ")]
                    ber = data["BER"]
                    errors = data["Errors"]
                    samples = data["Sample"]

                    data_point = (x, y)

                    if data_point in scan_points:
                        scan_point = scan_points[data_point]

                        # Combine existing BER with new BER
                        scan_point.ber += ber

                        # Combine errors if new error != 0 and old error == 0
                        if errors != 0 and scan_point.errors == 0:
                            scan_point.errors = errors

                    else:
                        scan_points[data_point] = ScanPoint(x, y, ber, errors, samples)

                self.scan_data.processed = Plot2DData(
                    scan_points=scan_points, ber_floor_value=ber_floor_value
                )

            if EYE_SCAN_PROGRESS in scan_report:
                self.progress = round(float(scan_report[EYE_SCAN_PROGRESS]), 2)

            if EYE_SCAN_STATUS in scan_report:
                self.status = scan_report[EYE_SCAN_STATUS]

            # If rich pkg is available send update
            common_progress.update(
                task_id=self._task_id,
                completed=int(self.progress),
                status=self._get_status(),
            )

            if self.status in {EYE_SCAN_ABORTED, EYE_SCAN_DONE}:
                # If scan is done create the plot
                if self.status == EYE_SCAN_DONE:
                    self.plot = EyeScanPlot(self)

                # If user has registered done callback function call it.
                if callable(self.done_callback):
                    try:
                        self.done_callback(self)
                    except Exception as e:
                        printer(
                            f"Unhandled exception during eye scan done callback!\n"
                            f"Exception - {str(e)}",
                            level="warning",
                        )

                self._scan_done_event.set()

            else:
                # If user has registered progress callback function call it.
                if callable(self.progress_callback):
                    try:
                        self.progress_callback(self.progress)
                    except Exception as e:
                        printer(
                            f"Unhandled exception during eye scan progress callback!\n"
                            f"Exception - {str(e)}",
                            level="warning",
                        )

        except Exception as e:
            printer(
                f"Unhandled scan update exception on TCF thread!\nException - {str(e)}",
                level="warning",
            )

    def wait_till_done(self):
        """
        Block current thread execution till the eye scan completes OR it is aborted by cs_server/HW.

        """
        if self._handle_from_cs_server is None:
            raise RuntimeError(f"Please start the scan before waiting for it to finish!")

        self._scan_done_event.wait()
        self._handle_from_cs_server = None

    def stop(self):
        """
        Stop eye scan, that is in-progress in the MicroBlaze

        """
        self.rx.core_tcf_node.terminate_eye_scan(rx_name=self.rx.handle)

    def generate_report(self):
        """
        Generate a report for this eye scan object and send it to the "printer" for printing

        """
        report = Table(title=f"{self.name} report", box=BOX_SQUARE)
        report.add_column("Property", justify="right")
        report.add_column("Value", justify="left")

        report.add_row(f"RX", f"{self.rx.handle}")
        report.add_row(f"Status", self._get_status())
        report.add_row(f"Progress", f"{self.progress}%")
        report.add_row(f"Start time", f"{self.start_time}")
        report.add_row(f"Stop time", f"{self.stop_time}")
        report.add_row(f"MB ELF version", f"{self.elf_version}")
        report.add_row(
            f"#Data points expected",
            f"{self.data_points_expected}",
        )
        report.add_row(f"#Data points read", f"{self.data_points_read}")

        report.add_row("", "")

        scan_params = Table(box=BOX_SQUARE)
        scan_params.add_column("Parameter", justify="right")
        scan_params.add_column("Value", justify="left")

        for param in self.params.values():
            scan_params.add_row(
                f"{param.name}",
                f"{param.default_value if param.value is None else param.value}",
            )

        report.add_row(f"Scan parameters", scan_params)

        printer("\n")
        printer(report)
        printer("\n")
