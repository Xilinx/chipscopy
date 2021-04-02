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
import shutil
import tempfile
import os


_function_text = """
import json

def _default_repr(obj):
    return repr(obj)

def _resolve_global(name):
    g = globals()
    return g[name] if name in g else None

"""


class NotebookResult:
    """Class representing the result of executing a notebook

    Contains members with the form ``_[0-9]*`` with the output object for
    each cell or ``None`` if the cell did not return an object.

    The raw outputs are available in the ``outputs`` attribute. See the
    Jupyter documentation for details on the format of the dictionary

    """

    def __init__(self, nb):
        self.outputs = [c["outputs"] for c in nb["cells"] if c["cell_type"] == "code"]
        objects = json.loads(self.outputs[-1][0]["text"])
        for i, o in enumerate(objects):
            setattr(self, "_" + str(i + 1), o)


def _create_code(num):
    call_line = "print(json.dumps([{}], default=_default_repr))".format(
        ", ".join(("_resolve_global('_{}')".format(i + 1) for i in range(num)))
    )
    return _function_text + call_line


def run_notebook(notebook, root_path=".", timeout=30, prerun=None):
    """Run a notebook in Jupyter

    This function will copy all of the files in ``root_path`` to a
    temporary directory, run the notebook and then return a
    ``NotebookResult`` object containing the outputs for each cell.

    The notebook is run in a separate process and only objects that
    are serializable will be returned in their entirety, otherwise
    the string representation will be returned instead.

    Parameters
    ----------
    notebook : str
        The notebook to run relative to ``root_path``
    root_path : str
        The root notebook folder (default ".")
    timeout : int
        Length of time to run the notebook in seconds (default 30)
    prerun : function
        Function to run prior to starting the notebook, takes the
        temporary copy of root_path as a parameter

    """
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    with tempfile.TemporaryDirectory() as td:
        workdir = os.path.join(td, "work")
        notebook_dir = os.path.join(workdir, os.path.dirname(notebook))
        shutil.copytree(root_path, workdir)
        if prerun is not None:
            prerun(workdir)
        fullpath = os.path.join(workdir, notebook)
        with open(fullpath, "r") as f:
            nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(kernel_name="python3", timeout=timeout)
        code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        nb["cells"].append(
            nbformat.from_dict(
                {"cell_type": "code", "metadata": {}, "source": _create_code(len(code_cells))}
            )
        )
        ep.preprocess(nb, {"metadata": {"path": notebook_dir}})
        return NotebookResult(nb)


def _default_repr(obj):
    return repr(obj)


class ReprDict(dict):
    """Subclass of the built-in dict that will display using the Jupyterlab
    JSON repr.

    The class is recursive in that any entries that are also dictionaries
    will be converted to ReprDict objects when returned.

    """

    def __init__(self, *args, rootname="root", expanded=False, **kwargs):
        """Dictionary constructor

        Parameters
        ----------
        rootname : str
            The value to display at the root of the tree
        expanded : bool
            Whether the view of the tree should start expanded

        """
        self._rootname = rootname
        self._expanded = expanded

        super().__init__(*args, **kwargs)

    def _repr_json_(self):
        return (
            json.loads(json.dumps(self, default=_default_repr)),
            {"expanded": self._expanded, "root": self._rootname},
        )

    def __getitem__(self, key):
        obj = super().__getitem__(key)
        if type(obj) is dict:
            return ReprDict(obj, expanded=self._expanded, rootname=key)
        else:
            return obj
