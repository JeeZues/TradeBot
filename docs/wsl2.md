# Linux (WSL2) on Windows 10
https://docs.microsoft.com/en-us/windows/wsl/install-win10


Open PowerShell as Administrator and run:
```
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```
restart computer

Download and install https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

Open PowerShell as Administrator and run:
```
wsl --set-default-version 2
```

From https://aka.ms/wslstore, install Linux (e.g. Ubuntu)

Launch installation, create username and password

```
mkdir -P git/jeezues
cd git/jeezues
git clone https://github.com/JeeZues/TradeBot.git
cd TradeBot

sudo apt update
sudo apt install pip3

pip3 install -r requirements.txt

cp RENAME_ME__run_config.py run_config.py
```
edit run_config.py using your favourit editor, e.g. vi, nano, etc.
```
python3 run.py -h
```
