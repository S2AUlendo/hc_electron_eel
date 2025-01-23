# Project Overview
A simple Python-Eel project.

## Requirements
• Python 3 installed.

## Usage
Use the following command to run the app:
```
python main.py
```

## Building Distributables
Create a single executable with:
```
 pyinstaller main.py --hidden-import bottle_websocket  --add-data "web;web" --add-data "web;electron/resources/app/web" --add-data "electron;electron" --add-data "main.js;electron/resources/app" --add-data "preload.js;electron/resources/app" --add-data "package.json;electron/resources/app" --noconsole --onedir --icon=icon.ico   
```