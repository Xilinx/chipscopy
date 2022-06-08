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

import shutil
import os
import argparse
import sys
from distutils.dir_util import mkpath, copy_tree
from distutils.file_util import copy_file
from pathlib import Path
from shutil import move
import chipscopy

SOURCE_EXAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(chipscopy.__file__), "examples"))
TARGET_EXAMPLE_DIR = os.path.join(".", "chipscopy-examples")


def _copy_and_move_files(files_to_copy, files_to_move):
    """Copy and move files and folders. ``files_to_copy`` and ``files_to_move``
    are expected to be dict where the key is the source path, and the value is
    destination path.
    """
    # copy files and folders
    for src, dst in files_to_copy.items():
        if os.path.isfile(src):
            mkpath(os.path.dirname(dst))
            copy_file(src, dst)
        else:
            copy_tree(src, dst)
    # and move files previously downloaded
    for src, dst in files_to_move.items():
        shutil.move(src, dst)


def deliver_examples(src_path, dst_fullpath, name):
    """Deliver examples to target destination path.

    Parameters
    ----------
        src_path: str
            The source path to copy from
        dst_fullpath: str
            The destination path to copy to
        name: str
            The name of the example module
    """
    files_to_copy = {}
    files_to_move = {}
    for root, dirs, files in os.walk(src_path):
        if ".ipynb_checkpoints" in dirs:
            dirs.remove(".ipynb_checkpoints")
        if "__init__.py" in files:
            files.remove("__init__.py")
        keepers = [".ipynb", ".py", ".pdi", ".ltx", ".png"]
        for f in files:
            extension = os.path.splitext(f)[1]
            if extension in keepers:
                # If folder is in the list of files to copy, remove it as it is
                # going to be inspected
                if root in files_to_copy:
                    files_to_copy.pop(root)
                relpath = os.path.relpath(root, src_path)
                relpath = "" if relpath == "." else relpath
                try:
                    files_to_copy_tmp = {}
                    files_to_move_tmp = {}
                    for d in dirs:
                        if d != "__pycache__":
                            dir_dst_path = os.path.join(dst_fullpath, relpath, d)
                            files_to_copy_tmp[os.path.join(root, d)] = dir_dst_path
                    for f2 in files:
                        file_dst_path = os.path.join(dst_fullpath, relpath, f2)
                        files_to_copy_tmp[os.path.join(root, f2)] = file_dst_path
                    files_to_copy.update(files_to_copy_tmp)
                    files_to_move.update(files_to_move_tmp)
                except FileNotFoundError as e:  # pragma: no cover
                    if relpath:
                        nb_str = os.path.join(name, relpath)
                        print(
                            "Could not resolve file '{}' in folder "
                            "'{}', examples will not be "
                            "delivered".format(str(e), nb_str)
                        )
    try:
        if not files_to_copy:
            print("The example module '{}' could not be delivered. ".format(name))
        else:
            _copy_and_move_files(files_to_copy, files_to_move)
    except (Exception, KeyboardInterrupt) as e:  # pragma: no cover
        print("Exception detected. Delivery process did not complete...")
        raise e


def find_examples(example_dir=SOURCE_EXAMPLE_DIR, full_path=False):
    examples_list = []
    for root, dirs, files in os.walk(example_dir):
        if ".ipynb_checkpoints" in dirs:
            dirs.remove(".ipynb_checkpoints")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        if "__init__.py" in files:
            files.remove("__init__.py")
        examples = [f for f in files if f.endswith(".ipynb") or f.endswith(".py")]
        if full_path:
            examples = [os.path.join(root, f) for f in examples]
        examples_list.extend(examples)
    return examples_list


class _GetExamplesParser(argparse.ArgumentParser):  # pragma: no cover
    @property
    def epilog(self):
        return "Available example modules: {}".format(", ".join(find_examples()))

    @epilog.setter
    def epilog(self, x):
        """Dont set epilog in Parser.__init__."""
        pass


def _get_examples_parser():  # pragma: no cover
    """Initialize and return the argument parser."""
    parser = _GetExamplesParser(description="Deliver available ChipScoPy examples")
    parser.add_argument(
        "-l", "--list", action="store_true", help="List available examples and exit"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force delivery even if target examples "
        "directory already exists. The existing "
        "directory will be renamed adding a timestamp",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="Specify a custom path to deliver examples to. "
        "Default is '{}'".format(TARGET_EXAMPLE_DIR),
    )
    parser.add_argument(
        "-y", "--assume_yes", action="store_true", help='Skip Interactive Prompts - assume "Yes"'
    )
    return parser


def main():  # pragma: no cover
    parser = _get_examples_parser()
    args = parser.parse_args()
    examples_list = find_examples()
    if args.list:
        if examples_list:
            print("Available examples:\n- {}".format("\n- ".join(examples_list)))
        else:
            print("No examples available")
            sys.exit(2)
    if not examples_list:
        print("No examples available, nothing can be delivered")
        sys.exit(2)
    if args.path:
        delivery_path = args.path
    else:
        delivery_path = TARGET_EXAMPLE_DIR
    yes = ["yes", "ye", "y"]
    no = ["no", "n"]
    nb_str = "\n- ".join([os.path.basename(nb) for nb in examples_list])
    print(
        f"The following examples  will be delivered to {os.path.abspath(delivery_path)}: \n- {nb_str}"
    )
    if not args.assume_yes:
        choice = input("Do you want to proceed? [Y/n] ").lower()
        while True:
            if choice == "" or choice in yes:
                break
            if choice in no:
                return
            choice = input("Please respond with 'yes' or 'no' (or 'y' or " "'n') ")

    # Check for read-only directory before trying to deploy example files.
    # This enables us to give an error message and exit early.
    # Tried using python tempfile but that hung on windows.

    try:
        canonical_path = os.path.abspath(delivery_path)
        base = Path(os.path.dirname(canonical_path))
        filename = "8f06bb29-b01b-42fe-9f8d-7aa48825a5b2"
        test_file = base / filename
        f = open(test_file, "w")
        f.close()
        test_file.unlink()
    except (OSError, IOError):
        print(
            f"\nDirectory '{base}' is read-only. Can not extract examples. "
            "Please change do a different directory with write access permissions."
        )
        sys.exit(3)

    if os.path.exists(delivery_path):
        if args.force:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
            backup_dir = os.path.split(delivery_path)[1] + "_" + timestamp
            backup_fullpath = os.path.join(os.path.dirname(delivery_path), backup_dir)
            move(delivery_path, backup_fullpath)
            print(f"Backing up existing examples to {backup_dir}")
        else:
            print(
                "Target examples directory already "
                "exists. Specify another path or use "
                "the 'force' option to proceed"
            )
            sys.exit(1)
    try:
        for example_name in examples_list:
            print(f"Delivering example '{os.path.basename(example_name)}'...")
            deliver_examples(SOURCE_EXAMPLE_DIR, delivery_path, example_name)
    except (Exception, KeyboardInterrupt) as e:
        raise e
    finally:
        if os.path.isdir(delivery_path) and len(os.listdir(delivery_path)) == 0:
            os.rmdir(delivery_path)
        if not os.path.isdir(delivery_path):
            print("No examples available")
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
