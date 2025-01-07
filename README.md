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
python -m eel main.py web --hidden-import bottle_websocket --add-data electron;electron --add-data main.js;electron/resources/app --add-data package.json;electron/resources/app --onefile --noconsole --debug all
```