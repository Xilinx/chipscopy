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

import re
from enum import Enum
from typing import Union, Optional

from typing_extensions import Final, Literal

from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.style import Style
from rich.console import Console
from rich.progress import Progress, TaskID, TextColumn, BarColumn


class Printer:
    def __init__(self):
        self.console = Console()

    @property
    def quiet(self):
        return self.console.quiet

    @quiet.setter
    def quiet(self, value):
        self.console.quiet = value

    def __call__(self, *args, level: Optional[Literal["info", "warning"]] = None):
        if isinstance(args[0], Table) or isinstance(args[0], Tree):
            self.console.print(args[0])
        elif len(args) == 1 and isinstance(args[0], str):
            if level is not None:
                self._print_msg(args[0], level=level)
            else:
                self.console.print(args[0])
        else:
            self.console.print(*args)

    def _print_msg(self, msg, *, level: Literal["info", "warning"]):
        custom_styles: Final[dict] = {
            "info": Style(bold=False),
            "warning": Style(color="yellow", bold=False, italic=True),
        }

        if level == "info":
            full_msg = Text("\n--> INFO: ", style=Style(bold=True))
        elif level == "warning":
            full_msg = Text("\n--> WARNING: ", style=Style(color="yellow", bold=True))
        else:
            raise ValueError(f"Unknown print level '{level}'")

        default_style = custom_styles[level]

        msgs = msg.split("\n")

        full_msg.append(msgs[0], style=default_style)

        if len(msgs) > 1:
            for msg in msgs[1:]:
                original_msg = msg
                newline_chars = "\n"

                if msg.startswith("\n"):
                    match = re.match("^(\\n+)(.*)", msg)
                    newline_chars, original_msg = match.groups()

                # This is for aligning the current line with the first line of the message
                msg = f"{newline_chars}{' ' * 4}{original_msg}"
                full_msg.append(msg, style=default_style)

        self.console.print(full_msg)


printer = Printer()


class PercentProgressBar:
    class Status(Enum):
        DONE = "[bold green]Done[/]"
        ABORTED = "[bold red]Aborted[/]"
        STARTING = "[bold yellow]Starting[/]"
        IN_PROGRESS = "[bold blue]In Progress[/]"

    def __init__(self):
        self.progress_meter = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%", style="bold bright_magenta"),
            TextColumn("{task.fields[status]}"),
            console=printer.console,
            auto_refresh=False,
        )
        self.task_id: TaskID = None

    def add_task(
        self,
        *,
        total: int = 100,
        status: Union[str, Status],
        visible: bool = True,
        description: str,
    ):
        self.task_id: TaskID = self.progress_meter.add_task(
            description,
            total=total,
            status=status if isinstance(status, str) else status.value,
            visible=visible,
        )

        # Start the progress meter everytime we add a task.
        # If its already running, rich knows nothing needs to be done
        self.progress_meter.start()

        return self.task_id

    def update(
        self,
        *,
        status: Union[str, Status],
        task_id: TaskID = None,
        completed: int = None,
    ):
        if task_id is None:
            if self.task_id is None:
                return
            task_id = self.task_id

        kwargs = {"refresh": True, "status": status if isinstance(status, str) else status.value}
        if completed is not None:
            kwargs["completed"] = completed

        self.progress_meter.update(task_id, **kwargs)

        if kwargs["status"] in {
            PercentProgressBar.Status.DONE.value,
            PercentProgressBar.Status.ABORTED.value,
        }:
            if self.progress_meter.finished:
                self.progress_meter.stop()


if __name__ == "__main__":
    printer("\n\nJust your normal print. Nothing special to see here...")

    printer("Hello there, this is an INFO message", level="info")
    printer("Hello there\nThis is an INFO message\nspread over multiple lines", level="info")
    printer(
        "Hello there\nThis is an INFO message\n"
        "spread over multiple lines\n\nwith blank lines in between",
        level="info",
    )

    printer("Hello there, this is a WARNING message", level="warning")
    printer("Hello there\nThis is an WARNING message\nspread over multiple lines", level="warning")
    printer(
        "Hello there\nThis is a WARNING message\n"
        "spread over multiple lines\n\nwith blank lines in between",
        level="warning",
    )

    printer("\n")

    import threading
    import time

    def func1(task_id, sleep_time):
        x = 0
        while True:
            time.sleep(sleep_time)
            progress_meter.update(task_id=task_id, status="In Progress", completed=x)
            x += 1

            if x > 100:
                break

        progress_meter.update(task_id=task_id, status="Done")

    progress_meter = PercentProgressBar()
    task_id1 = progress_meter.add_task(
        description=f"Thread 1 progress ",
        status="Starting",
    )

    t1 = threading.Thread(target=func1, args=(task_id1, 0.1))
    t1.start()

    task_id2 = progress_meter.add_task(
        description=f"Thread 2 progress ",
        status="Starting",
    )

    t2 = threading.Thread(target=func1, args=(task_id2, 0.2))

    t2.start()

    t1.join()
    t2.join()

    printer.quiet = True

    printer("You shouldn't see this message, because the printer is turned off")
