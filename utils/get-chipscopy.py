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
import subprocess as sp
import sys
import os
import re
from urllib import request
import platform


def create_venv_launcher(home_dir, venv_path, venv, system):
    shortcut = f"{home_dir}{os.sep}Desktop{os.sep}{venv}"
    if system == "Windows":
        activate_cmd = f"{venv_path}{os.sep}Scripts{os.sep}Activate.ps1"
        # build script to create lnk
        ps_command = f"""
                      $WScriptShell = New-Object -ComObject WScript.Shell
                      $ShortCut = $WScriptShell.CreateShortcut("{shortcut}.lnk")
                      $ShortCut.TargetPath = "powershell.exe"
                      $ShortCut.Arguments = "-noexit invoke-expression -Command {activate_cmd}"
                      $ShortCut.Save()
                      """
        proc = sp.Popen(["powershell.exe"], stdin=sp.PIPE)
        proc.communicate(input=ps_command.encode())
        proc.kill()
    elif system == "Linux":
        # get icons
        logo_path = f"{venv_path}{os.sep}/python-logo-tm.png"
        sp.check_call(
            ["wget", "https://www.python.org/static/img/python-logo.png", "-O", logo_path]
        )
        launcher_spec = [
            f"[Desktop Entry]",
            "Version=1.0",
            "Type=Application",
            "Terminal=true",
            f"Name={venv}",
            f"GenericName={venv}",
            f"Comment={venv} desktop launcher",
            "Categories=",
            "X-KeepTerminal=true",
            f"Icon={logo_path}",
            f'Exec=gnome-terminal --tab --title="{venv}" --command="bash --init-file '
            + f'{venv_path}{os.sep}bin{os.sep}activate"',
        ]
        with open(f"{home_dir}{os.sep}Desktop{os.sep}{venv}.desktop", "w") as ofh:
            for line in launcher_spec:
                ofh.write(line + "\n")


def python_setup(system):
    # \d in regex ensures we can convert to int later
    version_matcher = re.compile(r"^Python (?P<major>\d+)\.(?P<minor>\d+)\..+$")
    acceptable_python = False

    raw_version = sp.check_output(
        f"{sys.executable} --version", stderr=sp.STDOUT, shell=True
    ).decode("utf-8")

    match = version_matcher.match(raw_version.strip())
    if match:
        ver_maj = int(match.group(1))
        ver_min = int(match.group(2))
        if ver_maj < 3 or (ver_maj == 3 and ver_min < 7):
            print(
                f"ERROR: Python 3.7 or newer is required by chipscopy, found: {ver_maj}.{ver_min}"
            )
        else:
            acceptable_python = True

    if not acceptable_python:
        print("Could not locate a suitable python3 on your system")
        print()
        if system == "Windows":
            print(f"  Windows users may install a valid python through the Microsoft store")
            print(f"  or download a installer from https://python.org")
        elif system == "Linux":
            print(
                f"  If Vivado (2021.1+) is installed then there is a suitable python available to Linux users."
            )
            print(
                f"    Alternatively, python source may be obtained from https://python.org, and compiled"
            )
        print()
        print()
        raise NotImplementedError("Invalid python, please re-run this script using a valid python")


def pip_config(cert_dir):
    """
    build certificate bundle that includes the Xilinx X.509 Certificate Authorities
    configure pip to use this bundle and to search the xilinx internal pypi server
    :param cert_dir: location to create new certificate bundle
    :return: None
    """
    print("Configuring Pip for Xilinx Packages")
    print(f"certs dir: {cert_dir}")
    if os.path.exists(cert_dir):
        ok_to_delete = (
            input(f"Directory {cert_dir} already exists, delete and rebuild? ([y]/n): ") or "y"
        )
        if ok_to_delete.lower() in ["n", "no"]:
            ok_to_delete = False
        else:
            ok_to_delete = True
        if ok_to_delete:
            shutil.rmtree(cert_dir)
            os.mkdir(cert_dir)
        else:
            print(
                "Will not create a new certificate bundle, pip config will not be modified, build_venv may not work"
            )
            return
    else:
        os.mkdir(cert_dir)
    sp.check_call(
        [sys.executable, "-m", "pip", "install", "--user", "--isolated", "certifi", "wheel"]
    )
    # TODO: modify path? with wheel exe
    ca_path = sp.check_output([sys.executable, "-m", "certifi"]).decode("utf-8").strip()
    shutil.copy(ca_path, f"{cert_dir}{os.sep}cert.pem")
    for cert_url in ["XLNX-ISSUINGCA01.pem", "XLNX-ISSUINGCA02.pem", "XLNX-ROOTCA.pem"]:
        with request.urlopen(f"https://web/cdp/{cert_url}") as response:
            with open(f"{cert_dir}{os.sep}cert.pem", "ab") as ofh:
                ofh.write(response.read())

    # now modify pip config to use new certificate bundle and search xilinx internal pypi server
    sp.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "config",
            "--user",
            "set",
            "global.extra-index-url",
            "https://artifactory.xilinx.com/artifactory/api/pypi/pypi/simple",
        ]
    )
    sp.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "config",
            "--user",
            "set",
            "global.cert",
            f"{cert_dir}{os.sep}cert.pem",
        ]
    )


def build_venv(home_dir, activate_script, examples_installer, python_binary_name, system):
    dfl_venvs_home = f"{home_dir}{os.sep}venvs{os.sep}"
    venvs_home = (
        input(f"Location for virtual environments? ([{dfl_venvs_home}]): ") or dfl_venvs_home
    )
    if venvs_home[-1] != os.sep:
        venvs_home += os.sep
    dfl_venv = "chipscopy"
    venv = input(f"Name for the new venv? ([{dfl_venv}]): ") or dfl_venv
    venv_path = f"{venvs_home}{venv}"
    venv_python_path = f"{venv_path}{os.sep}{python_binary_name}"

    new_venv = False
    rebuild_env = False
    if os.path.exists(venv_path):
        rebuild = input(f"Venv [{venv_path} already exists, rebuild? ([y]/n): ") or "y"
        if rebuild.lower() in ["no", "n"]:
            rebuild_env = False
        else:
            rebuild_env = True
        if rebuild_env:
            print("removing existing venv")
            shutil.rmtree(venv_path)
    else:
        new_venv = True
    if new_venv or rebuild_env:
        print("creating venv")
        sp.check_call([sys.executable, "-m", "venv", venv_path])

    # now need to update pip, install chipscopy, ...
    chipscopy_get_examples = f"{venv_path}{os.sep}{examples_installer}"
    print("upgrading pip")
    sp.check_call([venv_python_path, "-m", "pip", "install", "--upgrade", "pip"])
    print("installing chipscopy and dependencies")
    sp.check_call(
        [venv_python_path, "-m", "pip", "install", "chipscopy[jupyter,pandas,plotly,noc]"]
    )
    # finally get the examples
    print("extracting chipscopy examples")
    example_ext_dir = (
        input(
            f"Location to extract chipscopy examples? "
            + f"([{home_dir}{os.sep}chipscopy-examples]): "
        )
        or f"{home_dir}{os.sep}chipscopy-examples"
    )

    try:
        return_code = sp.check_call(
            [chipscopy_get_examples, "-y", "-p", example_ext_dir, "-f"], cwd=home_dir
        )
        if return_code != 0:
            print(
                "WARNING: examples delivered in this release were not delivered, run 'chipscopy-get-examples'"
            )
            print(f"  manually to fix the issue")
            print(f"  sub-call rc: {return_code}")
            successful_extraction = False
        else:
            successful_extraction = True
    except sp.CalledProcessError:
        print(
            "WARNING: examples delivered in this release were not delivered, run 'chipscopy-get-examples'"
        )
        print(f"  manually to fix the issue")
        successful_extraction = False

    print("")
    print("Virtual Environment Setup Complete")
    print("")
    print(f"  Your virtual environment named {venv} is located at: {venv_path}")
    print("")
    if system == "Windows":
        print(f"  PowerShell:")
        print(f"    Activate it by: ' {venv_path}{os.sep}{activate_script} '")
        print(f"    Deactivate via: ' deactivate '")
        print()
        print(f"  Command Console:")
        print(f"    Activate it by: ' {venv_path}{os.sep}activate.bat '")
    elif system == "Linux":
        print(f"    Activate it by: ' . {venv_path}{os.sep}{activate_script} '")
    print(f"    Deactivate via: ' deactivate '")
    print("")
    print("")
    if successful_extraction:
        print(f"  ChipScoPy Examples:")
        print(f"    The chipscopy examples were installed into: {example_ext_dir}")
        print(f"    It's recommended you start by exploring the deployed examples")
        print("")
    print(f"  Jupyter Notebook:")
    print(
        f"    Use this command in the future to relaunch jupyter. Ensure your environment is active!"
    )
    print(f"    ({venv})> jupyter-notebook {example_ext_dir}")
    create_shortcut = (
        input(
            "Create a shortcut on the desktop to launch the new environment in the future? (y/[n]): "
        )
        or "n"
    )
    if create_shortcut.lower() in ["yes", "y"]:
        create_venv_launcher(home_dir, venv_path, venv, system)
    print("")
    print("")
    print("-----------------------------------------------------------")

    launch_jupyter = input("Would you like to start jupyter now? (y/[n]): ") or "n"
    if launch_jupyter.lower() in ["yes", "y"]:
        print("Starting Jupyter")
        print()
        sp.check_call([venv_python_path, "-m", "jupyter", "notebook", example_ext_dir])


def main():
    system = platform.system()
    if system == "Windows":
        home_dir = os.getenv("USERPROFILE")
        activate_script = f"Scripts{os.sep}Activate.ps1"
        python_binary_name = f"Scripts{os.sep}python.exe"
        examples_installer = f"Scripts{os.sep}chipscopy-get-examples.exe"
    elif system == "Linux":
        sys.stdin = open("/dev/tty")
        home_dir = os.getenv("HOME")
        activate_script = "bin/activate"
        python_binary_name = f"bin/python"
        examples_installer = f"bin/chipscopy-get-examples"
    else:
        raise NotImplemented(f"OS {system} not supported")

    cert_dir = f"{home_dir}{os.sep}certificates"

    # banner
    print()
    print("--------------------------------------------")
    print("Welcome to the ChipScoPy Automated Installer")
    print("--------------------------------------------")
    print()
    print("  When prompted for input, you may supply a value, ")
    print(
        "  or simply press enter to accept the default value, denoted in square brackets [default-value]"
    )
    print()
    print()
    python_setup(system)
    # pip_config(cert_dir)
    build_venv(home_dir, activate_script, examples_installer, python_binary_name, system)


if __name__ == "__main__":
    main()
