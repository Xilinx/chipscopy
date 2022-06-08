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

import csv
import math
import re
from math import exp, log
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from chipscopy.utils.printer import printer

try:
    import kaleido
    import plotly as px
    import plotly.graph_objs as go

    _plotly_available = True
except ImportError:
    _plotly_available = False

try:
    from IPython import get_ipython
    from IPython.display import Image, display

    _jupyter_available = True
except ImportError:
    get_ipython = None
    Image = None
    display = None
    _jupyter_available = False

from chipscopy.api.ibert.aliases import EYE_SCAN_HORZ_RANGE

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.eye_scan import EyeScan


def check_for_plotly():
    if not _plotly_available:
        raise ImportError(
            f"Plotting packages not installed! Please run 'pip install chipscopy[core-addons]'"
        )


def check_for_jupyter():
    if not _jupyter_available:
        raise ImportError(
            f"Jupyter packages not installed! Please run 'pip install chipscopy[jupyter]'"
        )


def is_running_notebook():
    try:
        check_for_jupyter()
        shell = get_ipython().__class__.__name__
    except ImportError:
        shell = None
    except NameError:
        shell = None
    if shell == "ZMQInteractiveShell":
        return True
    else:
        return False


class EyeScanPlot:
    """
    Container for eye scan plot
    """

    def __init__(self, eye_scan):
        self.eye_scan: EyeScan = eye_scan
        """Link to the `EyeScan` object"""

        self.fig: go.Figure = None
        """Plotly `Figure` object"""

        self._x: List[float] = list()
        self._y: List[int] = list()
        self._z: List[List[float]] = list()

    def _clear_out_data(self):
        self._x, self._y, self._z = list(), list(), list()

    def _generate(self, *, title=""):
        if title == "":
            title = f"{self.eye_scan.rx.handle} ({self.eye_scan.name})"

        self._clear_out_data()

        if self.eye_scan.scan_data.processed is None:
            raise RuntimeError(
                f"No plot data received from server! "
                f"This might be because the scan did not finish successfully."
            )

        xs, ys = set(), set()
        for point in self.eye_scan.scan_data.processed.scan_points:
            xs.add(point[0])
            ys.add(point[1])

        self._x = sorted(xs)
        self._y = sorted(ys)

        # This will be needed later on to generate the legend
        min_ber, max_ber, plot_z_to_ber = -1234, -1234, list()

        for y in self._y:
            row_vals = list()
            z_hovertext_row = list()
            for x in self._x:
                ber = self.eye_scan.scan_data.processed.scan_points[(x, y)].ber
                val = log(ber, 10)
                hovertext = format(pow(10, val), ".2e")
                z_hovertext_row.append(hovertext)
                row_vals.append(val)

            curr_min = min(row_vals)
            if min_ber == -1234 or curr_min < min_ber:
                min_ber = curr_min

            curr_max = max(row_vals)
            if max_ber == -1234 or curr_max > max_ber:
                max_ber = curr_max

            self._z.append(row_vals)
            plot_z_to_ber.append(z_hovertext_row)

        extracted_data = re.match(
            r"^(.*) UI to (.*) UI$", self.eye_scan.scan_data.all_params[EYE_SCAN_HORZ_RANGE]
        )
        max_horz_range_ui, min_horz_range_ui = (
            float(extracted_data.group(1)),
            float(extracted_data.group(2)),
        )

        max_horz_range_codes, min_horz_range_codes = max(self._x), min(self._y)
        for index, x_in_codes in enumerate(self._x):
            self._x[index] = min_horz_range_ui + (
                ((x_in_codes - min_horz_range_codes) * (max_horz_range_ui - min_horz_range_ui))
                / (max_horz_range_codes - min_horz_range_codes)
            )

        # Generate BER to z mapping for colorbar a.k.a legend
        colorbar_number_of_ticks: int = math.floor(min_ber)

        incr_factor = (max_ber - min_ber) / (colorbar_number_of_ticks - 1)

        color_bar_tick_text = list()
        color_bar_tick_values = list()
        # for x_factor in range(colorbar_number_of_ticks):
        #     val = min_ber + (x_factor * incr_factor)
        #     color_bar_tick_values.append(val)
        #     tick_text = format(pow(base, val) if base != 0 else exp(val), ".2e")
        #     color_bar_tick_text.append(tick_text)
        for i in range(-1, math.floor(min_ber) - 1, -1):
            color_bar_tick_text.append(format(pow(10, i), ".0e"))
            color_bar_tick_values.append(i)

        contour = go.Contour(
            x=self._x,
            y=self._y,
            z=self._z,
            line=dict(smoothing=0.85, width=0),
            colorbar=dict(
                nticks=abs(math.floor(min_ber)),
                ticks="outside",
                tickmode="array",
                tickvals=color_bar_tick_values,
                ticktext=color_bar_tick_text,
                title=dict(text="BER"),
            ),
            contours=dict(start=-1, end=math.floor(min_ber), size=0.5),
            colorscale="portland",
            hovertext=plot_z_to_ber,
            hoverinfo="x+y+text",
        )

        x_axis_options = dict(zeroline=False, title="UI", mirror=True)
        y_axis_options = dict(zeroline=False, title="Voltage (Codes)", mirror=True)
        layout = go.Layout(xaxis=x_axis_options, yaxis=y_axis_options)

        self.fig = go.Figure(layout=layout, data=contour)

        self.fig.update_layout(title=dict(text=title))

    def show(self, display_type: str = "automatic", *, title: str = ""):
        """
        Displays the plot in the browser

        Args:
            display_type: image format to show. Options are automatic, static, dynamic. Default is 'automatic'
            title: title to display in plot

        """
        check_for_plotly()

        self._generate(title=title)

        if display_type == "automatic":
            if is_running_notebook():
                display_type = "static"
            else:
                display_type = "dynamic"

        if display_type == "dynamic":
            self.fig.show()
        elif display_type == "static":
            check_for_jupyter()
            image_bytes = self.fig.to_image(format="png")
            ipython_image = Image(image_bytes)
            display(ipython_image)
        else:
            raise ValueError("show: display_type must be automatic, static, or dynamic")

    def save(
        self, path: str = ".", file_name: str = None, *, file_format: str = "svg"
    ) -> Optional[str]:
        """
        Save plot to a file

        Args:
            path: **(Optional)** Location where file should be saved.

            file_name: **(Optional)** Name of the file

            file_format: **(Optional)** File format. Default is `SVG`

        Returns:
            Path of the saved plot

        """
        check_for_plotly()

        output_path = Path(path)

        if file_name is None:
            file_name = f"{self.eye_scan.name}"

        output_path = output_path.joinpath(f"{file_name}.{file_format}")

        self._generate()
        self.fig.write_image(str(output_path.resolve()), height=1080, width=1920, scale=1)

        printer(f"Saved eye scan plot to {str(output_path.resolve())}", level="info")

        return str(output_path.resolve())


class EyeScanImporter:  # pragma: no cover
    @staticmethod
    def load_from_vivado_csv(file_path: Path = None):
        if file_path is None:
            file_path = Path()

        def normalize_codes_to_ui(data, min_range, max_range):
            min_element, max_element = min(data), max(data)
            for index, value in enumerate(data):
                data[index] = min_range + (
                    ((value - min_element) * (max_range - min_range)) / (max_element - min_element)
                )

        x_axis, y_axis, scan_data = list(), list(), list()
        with file_path.open("r") as csv_file:
            csv_file_contents = csv.reader(csv_file)
            for row in csv_file_contents:
                if row[0] == "Horizontal Range":
                    split = row[1].split()
                    min_value_range, max_value_range = (float(split[0]), float(split[-2]))
                elif row[0] == "Scan Start":
                    for index, row in enumerate(csv_file_contents):
                        if row[0] == "Scan End":
                            break
                        if not x_axis:
                            x_axis = [float(value) for value in row[1:]]
                            normalize_codes_to_ui(x_axis, min_value_range, max_value_range)
                            continue
                        y_axis.append(float(row[0]))
                        scan_data.append([log(float(value)) for value in row[1:]])

        return x_axis, y_axis, scan_data
