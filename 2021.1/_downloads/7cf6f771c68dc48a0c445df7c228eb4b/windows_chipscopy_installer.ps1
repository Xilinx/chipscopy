# Script to help with chipscopy installation on windows 10

function Python-Setup {
    do {
        $valid_python = 0
        $python_exe = Get-Command python
        if($?)
        {
            $version = Invoke-Expression "python -V"
            $version_int = $version.Split(" ")[1]
            $ver_maj = $version_int.Split(".")[0]
            $ver_maj = $ver_maj -as [int]
            $ver_min = $version_int.Split(".")[1]
            $ver_min = $ver_min -as [int]
            $ver_comp = $version_int.Split(".")[2]
            $ver_comp = $ver_comp -as [int]
            Write-Host "Version info: ${version_int}, maj ${ver_maj}, min ${ver_min}, comp ${ver_comp}"
            if($ver_maj -lt 3)
            {
                Write-Host "python 3.7 or newer is required"
            }
            else {
                if($ver_maj -eq 3 -and $ver_min -lt 7)
                {
                    Write-Host "python 3.7 or newer is required"
                }
                else {
                   # Acceptable python version
                    $valid_python = 1
                }
            }
        }
        if ($valid_python -ne 1)
        {
            Write-Host "Could not locate a suitable python3 on your system"
            Write-Host ""
            Write-Host "  NOTE: If Vivado (2020.2+) is installed on this machine then there is a suitable python already installed."
            Write-Host "    (typically) C:\Xilinx\<version>\tps\win64\python-X.Y.Z"
            Write-Host "  If Vivado is not installed a valid python may be obtained from https://python.org"
            Write-Host ""
            $python_loc = Read-Host -Prompt 'Please enter the PATH location for python (version 3.7+ required)'
            Write-Host "python PATH: ${python_loc} "
            $env:Path += ";${python_loc}"
            Get-Command python
        }
    } while($valid_python -ne 1)
}

function Build-Venv
{
    if (-not (Test-Path env:VENV_HOME))
    {
        # Write-Host "venv-home not set"
        $dfl_venv_home = "${HOME}\venvs"
    } else {
        $dfl_venv_home = $env:VENV_HOME
    }
    if (!($venv_dir = Read-Host "Location for virtual environments [$dfl_venv_home]")) { $venv_dir = $dfl_venv_home}
    $dfl_venv_name = "chipscopy"
    if (!($venv_name = Read-Host "Name for new env? [$dfl_venv_name]")) { $venv_name = $dfl_venv_name}
    $dfl_rebuild = "Y"
    $rebuild = "Y"
    if (Test-Path -Path "${venv_dir}\${venv_name}")
    {
        Write-Host "WARNING: virtual env ${venv_dir}\${venv_name} already exists!"
        if (!($rebuild = Read-Host "Rebuild? Y-rebuild, n-reuse (Y/n)?")) { $rebuild = $dfl_rebuild}
    }
    if("$rebuild" -eq "$dfl_rebuild")
    {
        if (Test-Path -Path "${venv_dir}\${venv_name}")
        {
            Remove-Item -Recurse -Force "${venv_dir}\${venv_name}"
        }
        Write-Host "Creating virtual environment in ${venv_dir}\${venv_name}"
        if (-not(Test-Path -Path "${venv_dir}"))
        {
            mkdir "${venv_dir}"
        }
        Push-Location "${venv_dir}"
        python -m venv ${venv_name}
        Pop-Location
    }

    Push-Location "${venv_dir}\${venv_name}"
    . ".\Scripts\Activate.ps1"
    python -m pip install --upgrade pip
    python -m pip install chipscopy[jupyter]
    Pop-Location

    Write-Host "Virtual Environment Setup Complete"
    Write-Host ""
    Write-Host ""
    Write-Host ""
    Write-Host "  Your new environment is located at: ${venv_dir}\${venv_name}"
    Write-Host "  Activate it by: ' ${venv_dir}\${venv_name}\Scripts\Activate.ps1 '"
    Write-Host "  Deactivate via: ' deactivate '"
}

Python-Setup
Build-Venv
