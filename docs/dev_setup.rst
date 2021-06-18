..
  Copyright 2021 Xilinx, Inc.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

Developer Installation
======================

This installation method is crafted for Python developers who intend to play an active development role for the
ChipScoPy project. For other intended uses, the other setup options are more appropriate, please see the top level
documentation for links to those install methods.

.. warning:: No matter which configuration of Python is used, **NEVER** invoke ``sudo``. Best case, you don't get what
             you want, worst case you will corrupt your operating system.

For this documentation it's assumed you've got a python installation available on your system. There are lots of options
so we can't cover all of them. Of note, the internal Xilinx Development team uses PyCharm from Jetbrains. We think it
rocks, but if you have another preferred development environment, go for it.

Install Git
___________

ChipScoPy uses ``git`` for version management. If your system doesn't have it (looking at you Windows) you will need to
install it.

Installing Git for Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^

Any Git that supports the most popular command set should work. Rule of thumb: >2.x should be fine. One such tool that
is confirmed to work with this project is `Git for Windows <https://git-scm.com/>`_.
To install grab `this <https://git-scm.com/download/win>`_ self extracting installer.

When the install wizard asks about adjusting the path, ensure you select **EITHER** the second choice "Git from the
command line and also from 3rd-party software" **OR** the third choice "Use Git and optional Unix tools from the Command
Prompt." It is this author's opinion that the 3rd option offers the most utility, but not strictly required for
ChipScoPy development on Windows. The first option will cause issues during ``poetry install``.

.. figure:: images/git_install_options.jpg
    :width: 250px
    :align: center
    :height: 200px
    :figclass: align-center

Click through the rest of the install wizard. Read the options--they matter, but the defaults are sufficient for the
ChipScoPy project.

Installing Git for Linux
^^^^^^^^^^^^^^^^^^^^^^^^

Consult your distribution's User's Manual. ``apt``, ``yum``, ``pacman``, etc.


Poetry
------

.. code-block:: none

    Twas first light when I saw her face upon the heath,
    and hence did I return,
    day-by-day, entranced,
    tho' vinegar did brine my heart, never...


Ok, so not that kind of poetry. `Poetry <https://python-poetry.org/>`_ is used by ChipScoPy for version, dependency, and
release management.

Install poetry, by following their `setup instructions <https://python-poetry.org/docs/#installation>`_.

On Windows, launch the git bash shell and run the curl command from the setup instructions. For Linux, simply launch a
terminal and run the install.


Clone Project
_____________

Either through your IDE or using the terminal, you'll need to clone the project.


.. code-block:: shell


    git clone git@github.com:Xilinx/chipscopy.git <optional_local_name>



If ``<optional_local_name>`` is omitted then the project will be cloned into the local directory `chipscopy.` Another thing to
note the repo is read-only for non team members. To contribute there will be a guide on how to submit patches for
review to the team. It will most likely require forking the repo and submitting pull requests from the downstream to
main.


Install Dependencies
____________________

Finally we'll use poetry to grab the required dependencies. This command must be executed from the top-level of project,
where the requisite file pyproject.toml can be located.

.. code-block:: shell


    poetry install


That's all that's required. This will install the locked versions--a pretty sure bet that things will work!

This completes the developer setup.
