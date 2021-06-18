#!/bin/bash


function python_setup ()
{
  python3=$(which python3)
  if ! $(which python3 -V); then
    echo "Could not locate a suitable python3 on your system"
    read -r -p "Please enter the location of the python3 installation: " python3
  fi
}

function build_venv ()
{
  if [ -z "${VENV_HOME}" ]; then
    DFL_VENV_HOME="${HOME}/venvs"
  else
    DFL_VENV_HOME=${VENV_HOME}
  fi
  read -r -p "Location for virtual environments? (${DFL_VENV_HOME}): " venv_dir
  venv_dir=${venv_dir:-${DFL_VENV_HOME}}
  read -r -p "Name for the new env? (chipscopy): " venv_name
  venv_name=${venv_name:-chipscopy}
  rebuild="Y"
  if [ -d "${venv_dir}/${venv_name}" ]; then
    read -r -p "Virtual env [${venv_dir}/${venv_name} already exists, Y-rebuild, n-reuse? (Y/n): " rebuild
    rebuild=${rebuild:-Y}
  fi
  if [ "${rebuild}" == "Y" ]; then
    rm -rf "${venv_dir:?}/${venv_name}"
    echo "Creating virtual environment in ${venv_dir}/${venv_name}"
    mkdir -p "${venv_dir}"
    pushd "${venv_dir}" || return
    ${python3} -m venv "${venv_name}"
    popd || return
  fi
  pushd "${venv_dir}/${venv_name}" || return
  . ./bin/activate
  python -m pip install --upgrade pip
  python -m pip install chipscopy[jupyter]
  popd || return

  echo "Virtual Environment Setup Complete"
  echo ""
  echo ""
  echo ""
  echo "  Your new environment is located at: ${venv_dir}/${venv_name}"
  echo "  Activate it by: ' source ${venv_dir}/${venv_name}/bin/activate '"
  echo "  Deactivate via: ' deactivate '"
}

python_setup
build_venv
