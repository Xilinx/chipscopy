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

import json
from math import ceil, sqrt, pow

# section Matplot lib
import matplotlib
from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.widgets import Button, RadioButtons

from chipscopy.api.noc.graphing.hbmmc import pc_map
from chipscopy.dm.harden.noc_perfmon.noc_types import ddrmc_main_typedef, hbmmc_typedef
from chipscopy.api.noc.noc_perfmon_utils import (
    PerfTGController,
    NoCElement,
    get_noc_typedef_from_name,
)

# use this for Qt5
matplotlib.use("Qt5Agg")
# this if for kivy
# matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
# matplotlib.use('kivy.garden.matplotlib.bickend_kivy')
import matplotlib.pyplot as plt
import matplotlib as mpl

MIN_Y = 100


def is_row_start(col_count, index):
    # given col counts and an index return if it's a row start
    # 1-index is required
    if (index - 1) % col_count == 0:
        return True
    else:
        return False


def build_y_scale_labels(y_max, len_ay):
    # return the y-axis labels array
    scale = ""
    labels = ["0"]
    locations = [0]
    fm = mpl.ticker.EngFormatter(places=2)
    r = 1
    if 0 <= y_max < pow(1000, 1):
        # no scaling
        pass
    elif pow(1000, 1) <= y_max < pow(1000, 2):
        scale = "K"
        r = pow(1000, 1)
    elif pow(1000, 2) <= y_max < pow(1000, 3):
        scale = "M"
        r = pow(1000, 2)
    elif pow(1000, 3) <= y_max < pow(1000, 4):
        scale = "G"
        r = pow(1000, 3)
    elif pow(1000, 4) <= y_max < pow(1000, 5):
        scale = "T"
        r = pow(1000, 4)
    for x in range(1, len_ay):
        val = x / (len_ay - 1) * y_max
        # wradix = val/r
        wradix = fm(val)
        if x == 1:
            labels.insert(0, f"-{wradix}")
            locations.insert(0, -val)
        labels.append(f"{wradix}")
        locations.append(val)
    return labels, locations


class ViewButtonProcessor:
    def __init__(self, axes, label, plot):
        self.plot = plot
        self.label = label
        self.button = Button(axes, label)
        self.button.on_clicked(self.switch_view)

    def switch_view(self, event):
        self.plot.switch_view(self.label)


class MeasurementPlot:
    def __init__(
        self,
        enable_nodes,
        mock,
        mock_file="slice.json",
        figsize=None,
        kivy=False,
        tg: PerfTGController = None,
    ):
        self.enable_nodes = [x.lower() for x in enable_nodes]
        self.mock = mock
        self.mock_file = mock_file
        self.figsize = figsize
        self.kivy = kivy
        self.tg = tg
        self.first_render = True
        self.display_nodes = []  # because some views don't apply to all nodes
        self.alive = True
        self.switching = False
        self.errors_present = False

        self.listener = None
        self.ifh = None
        self.lineno = 0
        self.fig = None
        self.plots = {}
        self.backgrounds = {}
        self.subplots = {}
        self.error_text_boxes = {}
        self.refresh_count = 0
        self.num_elements = None
        self.mock_data = {}
        self.view = "bandwidth"
        self.previous = None
        self.pattern = "Write Linear"

        # matplotlib GC is zealous, hence:
        self.latency_button = None
        self.bandwidth_button = None
        self.view_buttons = []
        self.start_btn = None
        self.stop_btn = None
        self.back_btn = None
        self.pattern_group = None
        self.tg_setup_btn = None
        self.legend_line_map = {}
        self.units_radio = None
        self.pc_radio = None
        self.pc = "PC0"

        # special handling for MEM
        self.views = ["bandwidth", "latency"]
        for node in self.enable_nodes:
            if (
                get_noc_typedef_from_name(node) == ddrmc_main_typedef
                or get_noc_typedef_from_name(node) == hbmmc_typedef
            ):
                self.views.append("mem")
                break

    def get_incremental_data(self):
        if not self.mock:
            return self.listener.unique_elements, None
        else:
            if self.ifh is None:
                self.ifh = open(self.mock_file, "r")
            self.lineno += 1
            line = self.ifh.readline()
            temp = json.loads(line)
            self.mock_data.update(temp)
            noc_element_data = self.mock_data
            return noc_element_data, next(iter(temp.keys()))

    def build_graphs(self):
        if self.view == "bandwidth":
            unit = "B/s"
            bottom = 0.175
        elif self.view == "latency":
            self.units = "ns"
            bottom = 0.175
        elif self.view == "mem":
            unit = "counts"
            bottom = 0.175

        # special handling for MEM
        if self.view == "mem":
            self.display_nodes = []
            for node in self.enable_nodes:
                if (
                    get_noc_typedef_from_name(node) == ddrmc_main_typedef
                    or get_noc_typedef_from_name(node) == hbmmc_typedef
                ):
                    self.display_nodes.append(node)
        else:
            self.display_nodes = self.enable_nodes

        noc_element_data, _ = self.get_incremental_data()
        col_count = ceil(sqrt(len(self.display_nodes)))
        row_count = ceil(len(self.display_nodes) / col_count)
        if self.figsize is not None:
            self.fig = plt.figure(figsize=self.figsize)
        else:
            self.fig = plt.figure()

        plt.subplots_adjust(left=0.1, right=0.965, bottom=bottom, top=0.88, wspace=0.2, hspace=0.2)
        # plt.subplots_adjust(left=.05, right=.965, bottom=bottom, top=.88, wspace=.25, hspace=.2)

        # turn on interactive
        plt.ion()

        plt.get_current_fig_manager().set_window_title(f"Versal PerfMon {self.view} Plot")

        # TODO fixup
        all_found = False
        if self.mock:
            while not all_found:
                noc_element_data, _ = self.get_incremental_data()
                all_found = set(self.enable_nodes).issubset(set(noc_element_data.keys()))

        # unmap existing legend lines
        self.legend_line_map = {}
        # hook up handlers
        self.fig.canvas.mpl_connect("pick_event", self.on_pick)
        self.fig.canvas.mpl_connect("close_event", self.on_close)

        # special processing for latency view:
        if self.view == "latency":
            radio_ax = plt.axes([0.01, 0.01, 0.15, 0.15])
            self.units_radio = RadioButtons(radio_ax, ("ns", "clocks"))

            def latency_units(label):
                self.units = label

            self.units_radio.on_clicked(latency_units)

        # special processing for hbm (generally mem-subsys?)
        # 'mem' view in this plotter is a canary for there being hbm/ddrmc nodes (so always add the pc radio button)
        if self.view == "mem" or self.view == "bandwidth" and "mem" in self.views:
            radio_ax = plt.axes([0.01, 0.01, 0.15, 0.15])
            self.pc_radio = RadioButtons(radio_ax, tuple(pc_map.keys()))
            self.pc_radio.set_active(pc_map[self.pc])

            def pc_select(label):
                self.pc = label
                self.switch_view(self.view)  # call to rebuild with newly selected pc

            self.pc_radio.on_clicked(pc_select)

        plot_index = 0
        # for elem, storage in noc_element_data.items():
        for elem in self.display_nodes:
            storage = noc_element_data[elem]
            data = storage.samples
            if (
                len(storage.axis_metrics["left_axis"][self.view]) == 0
                and len(storage.axis_metrics["right_axis"][self.view]) == 0
            ):
                continue
            plot_index += 1
            if plot_index == 1:
                self.num_elements = len(next(iter(data.values())))
            sp = plt.subplot(row_count, col_count, plot_index)
            self.plots[elem] = {"left_axis": {}, "right_axis": {}}
            x = list(range(50))
            # for metric in storage.axis_metrics["left_axis"][self.view]:
            for metric in storage.get_axis_metrics("left_axis", self.view, self.pc):
                if self.view == "latency":
                    if self.units != "clocks":
                        # need to convert
                        tslide = noc_element_data[elem].tslide
                        counter_freq_mhz = noc_element_data[elem].counter_freq_mhz
                        converted_data = [
                            element * pow(2, tslide) * 1000 / counter_freq_mhz
                            for element in data[metric]
                        ]
                        lambda_plot = plt.plot(x, converted_data)[0]
                else:
                    lambda_plot = plt.plot(x, data[metric])[0]
                self.plots[elem]["left_axis"][metric] = lambda_plot

            lambda_plot = next(iter(self.plots[elem]["left_axis"].values()))
            lambda_plot.axes.set_xticks(range(0, self.num_elements)[::5])
            lambda_plot.axes.set_xticklabels([])

            # right axis metrics
            # for metric in storage.axis_metrics["right_axis"][self.view]:
            for metric in storage.get_axis_metrics("right_axis", self.view, self.pc):
                right_lambda_axes = lambda_plot.axes.twinx()
                r_lambda_plot = right_lambda_axes.plot(x, data[metric])[0]
                self.plots[elem]["right_axis"][metric] = r_lambda_plot

            if is_row_start(col_count, plot_index):
                if self.view == "latency":
                    sp.set_ylabel(f"{self.view}")
                else:
                    sp.set_ylabel(f"{self.view} - {unit}")

            for axis in ["left_axis", "right_axis"]:
                if len(self.plots[elem][axis].keys()) == 0:
                    continue
                lambda_plot = next(iter(self.plots[elem][axis].values()))
                data_max = max(
                    [max(data[x]) for x in storage.get_axis_metrics(axis, self.view, self.pc)]
                )
                new_y_max = max(data_max, MIN_Y)
                new_y_min = -0.1 * new_y_max
                new_y_max = 1.1 * new_y_max
                lambda_plot.axes.set_ylim((new_y_min, new_y_max))

            sp.set_title(f"{elem}")
            self.backgrounds[elem] = self.fig.canvas.copy_from_bbox(lambda_plot.axes.bbox)
            self.subplots[elem] = sp
            self.error_text_boxes[elem] = {}
            # legend
            legend_keys = []
            for axis in ["left_axis", "right_axis"]:
                for key in storage.get_axis_metrics(axis, self.view, self.pc):
                    legend_keys.append(key)
            leg = plt.legend(legend_keys)

            # hook up pickers for visibility toggling
            # TODO: right axis
            for legend_line, line_plot in zip(
                leg.get_lines(), self.plots[elem]["left_axis"].values()
            ):
                # enable p
                legend_line.set_picker(True)
                legend_line.set_pickradius(5)
                self.legend_line_map[legend_line] = line_plot

        # navigation buttons buttons
        offset = 0
        self.view_buttons = []
        for view in self.views:
            if view == self.view:
                continue
            # [left, bottom, width, height]
            button_axes = plt.axes([0.8 + offset, 0.025, 0.075, 0.05])
            offset += 0.1
            self.view_buttons.append(ViewButtonProcessor(button_axes, view, self))

        # TG setup page
        if self.tg is not None:
            # [left, bottom, width, height]
            tg_setup_ax = plt.axes([0.6, 0.025, 0.075, 0.05])
            self.tg_setup_btn = Button(tg_setup_ax, "TG Setup")
            self.tg_setup_btn.on_clicked(self.switch_to_tg_setup)

        # if not self.kivy:
        #     # plt.show()
        #     pass

        if self.first_render:
            plt.show()
            self.first_render = False

        self.fig.canvas.draw()

    # noinspection PyUnboundLocalVariable
    def update(self, node: NoCElement):
        if self.view == "tg_control":
            return

        # TODO mock-data?
        node_to_update = node
        noc_element_data, updated = self.get_incremental_data()
        if self.mock:
            node_to_update = updated

        elem = node.name
        data = node.samples

        self.fig.canvas.restore_region(self.backgrounds[elem])
        for metric, plot in self.plots[elem]["left_axis"].items():
            if self.view == "latency":
                if self.units != "clocks":
                    # need to convert
                    tslide = node.tslide
                    counter_freq_mhz = node.counter_freq_mhz
                    converted_data = [sample * 1000 / counter_freq_mhz for sample in data[metric]]
                    plot.set_ydata(converted_data)
                else:
                    plot.set_ydata(data[metric])
            else:
                plot.set_ydata(data[metric])

        for metric, plot in self.plots[elem]["right_axis"].items():
            plot.set_ydata(data[metric])

        for axis in ["left_axis", "right_axis"]:
            if len(self.plots[elem][axis].keys()) == 0:
                continue
            lambda_plot = next(iter(self.plots[elem][axis].values()))
            data_max = 0
            for metric in self.plots[elem][axis].keys():
                for line in self.plots[elem][axis][metric].axes.lines:
                    line_max = max(line.get_ydata())
                    if line_max > data_max:
                        data_max = line_max
            # data_max = max([max(data[x]) for x in self.plots[elem][axis][:]])
            new_y_max = max(data_max, MIN_Y)
            new_y_min = -0.1 * new_y_max
            new_y_max = 1.1 * new_y_max
            lambda_plot.axes.set_ylim((new_y_min, new_y_max))
            y_labels, y_locations = build_y_scale_labels(max(data_max, MIN_Y), 6)
            lambda_plot.axes.yaxis.set_major_locator(FixedLocator(y_locations))
            lambda_plot.axes.yaxis.set_major_formatter(FixedFormatter(y_labels))

        # flags - search for any flags in any channel in any visible sample
        error_flags = []
        for sample in data["flags"]:
            if len(sample) > 0:
                for error in sample:
                    if error not in error_flags:
                        error_flags.append(error)

        error_y = 0.1
        for error in error_flags:
            if error not in self.error_text_boxes[elem].keys():
                self.error_text_boxes[elem][error] = self.subplots[elem].text(
                    0.1,
                    error_y,
                    error,
                    size=10,
                    ha="left",
                    va="top",
                    bbox=dict(boxstyle="square", ec=(1.0, 0.5, 0.5), fc=(1.0, 0.8, 0.8)),
                    transform=self.subplots[elem].transAxes,
                )
            else:
                self.error_text_boxes[elem][error].set_visible(True)
            error_y += 0.1

        for error in self.error_text_boxes[elem].keys():
            if error not in error_flags:
                self.error_text_boxes[elem][error].set_visible(False)

        # not going to do dynamic xtick labels
        # plot.axes.set_xticks(range(0, self.num_elements), data['ts'])
        # plot.axes.set_xticklabels(data['ts'][::5], rotation=90)
        # self.fig.canvas.blit(plot.axes.clipbox)

        # Attempts to speed up plotting
        # plot.axes.draw_artist(plot.axes.patch)

        # failed to update xtick labels
        # plot.axes.draw_artist(plot.axes.get_xticks())

        # working in standalone app
        # plot.axes.draw_artist(plot)
        # self.fig.canvas.blit(plot.axes.bbox)

        # notebook trials
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        # self.fig.canvas.draw_idle() -- this didn't work

        # self.refresh_count += 1
        # if self.refresh_count % 100 == 0:
        #     self.fig.canvas.draw()
        #     self.refresh_count = 0

    def build_tg_controlboard(self):
        if self.figsize is not None:
            self.fig = plt.figure(figsize=self.figsize)
        else:
            self.fig = plt.figure()

        # turn on interactive
        plt.ion()

        # set the title
        plt.get_current_fig_manager().set_window_title(
            "DDR & NoC PerfMon Traffic Generator Control"
        )

        def on_pattern_select(label):
            self.pattern = label

        # [left, bottom, width, height]
        pattern_ax = plt.axes([0.4, 0.5, 0.2, 0.1])
        patterns = tuple(list(self.tg.supported_patterns))
        active_pattern_index = list(self.tg.supported_patterns).index(self.pattern)
        self.pattern_group = RadioButtons(pattern_ax, patterns, active=active_pattern_index)

        self.pattern_group.on_clicked(on_pattern_select)

        def on_start(event):
            self.tg.set_active_pattern(self.pattern)
            self.tg.program()
            self.tg.start()

        # [left, bottom, width, height]
        start_tg_ax = plt.axes([0.4, 0.025, 0.075, 0.05])
        self.start_btn = Button(start_tg_ax, "Start TG")
        self.start_btn.on_clicked(on_start)

        def on_stop(event):
            self.tg.stop()

        # [left, bottom, width, height]
        stop_tg_ax = plt.axes([0.5, 0.025, 0.075, 0.05])
        self.stop_btn = Button(stop_tg_ax, "Stop TG")
        self.stop_btn.on_clicked(on_stop)

        def on_back(event):
            # if self.previous == 'bandwidth':
            #     self.switch_to_bandwidth(event=event)
            # elif self.previous == 'latency':
            #     self.switch_to_latency(event=event)
            self.switch_view(self.previous)

        # [left, bottom, width, height]
        back_ax = plt.axes([0.6, 0.025, 0.075, 0.05])
        self.back_btn = Button(back_ax, "Back")
        self.back_btn.on_clicked(on_back)

        # if not self.kivy:
        #     # plt.show()
        #     pass

        self.fig.canvas.draw()

    def on_pick(self, event):
        # on the pick event, find the orig line corresponding to the
        # legend proxy line, and toggle the visibility
        legend_key = event.artist
        line_plot = self.legend_line_map[legend_key]
        vis = not line_plot.get_visible()
        line_plot.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines
        # have been toggled
        if vis:
            legend_key.set_alpha(1.0)
        else:
            legend_key.set_alpha(0.2)
        self.fig.canvas.draw()

    def on_close(self, evt):
        if not self.switching:
            self.alive = False

    def destroy(self):
        self.switching = True
        plt.close(self.fig)
        self.switching = False

    def switch_view(self, view):
        self.previous = self.view
        self.view = view
        self.destroy()
        self.build_graphs()

    def switch_to_latency(self, event):
        self.previous = self.view
        self.view = "latency"
        self.destroy()
        # self.build_latency_graphs()
        self.build_graphs()

    def switch_to_bandwidth(self, event):
        self.previous = self.view
        self.view = "bandwidth"
        self.destroy()
        # self.build_bandwidth_graphs()
        self.build_graphs()

    def switch_to_tg_setup(self, event):
        self.previous = self.view
        self.view = "tg_control"
        self.destroy()
        self.build_tg_controlboard()
