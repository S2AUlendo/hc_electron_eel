# Project Overview
HC python eel project.

## Deploymnent
Github actions to build distro, build installer with ISS and code signing with Azure.

## Requirements
- Python 3.8 installed
- Windows 32/64 bit

## Setup python env
```
python -m venv venv
.\venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller  # Ensure PyInstaller is installed in the virtual environment
```

## Debug app
Use the following command to run the app:
```
python main.py
```

## Building Distributables
Create a single executable with:
```
pyinstaller main.spec
```

## Code signing with Azure 
Docs: https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/
