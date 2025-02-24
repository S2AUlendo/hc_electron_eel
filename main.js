// Modules to control application life and create native browser window
const path = require('path');

const { app, BrowserWindow, Menu, ipcMain, dialog, globalShortcut } = require('electron');

const iconPath = path.join(__dirname, "web", "public", "icon.ico");

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 1024,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath
  })

  // and load the index.html of the app.
  mainWindow.loadURL('http://localhost:8000/templates/app.html');

  mainWindow.setMinimumSize(1024, 1024);
  // Open the DevTools.
  // mainWindow.webContents.openDevTools()

  // Emitted when the window is closed.
  mainWindow.on('close', async (e) => {
    e.preventDefault(); // Always prevent immediate close

    try {
      const isRunning = await new Promise((resolve) => {
        ipcMain.once('mp-running-response', (_, status) => resolve(status))
        mainWindow.webContents.send('check-mp-running')
      });

      if (isRunning) {
        const choice = dialog.showMessageBoxSync(mainWindow, {
          type: 'warning',
          title: 'Warning',
          message: 'You have a file currently being processed, are you sure you want to quit?',
          buttons: ['Yes', 'No'],
          defaultId: 1
        });

        console.log("choice", choice)
        if (choice === 1) return; // Cancel close
      }
    } catch (error) {
      console.error(error);
    }

    if (terminalWindow) {
      terminalWindow.close();
    }

    if (viewWindow) {
      viewWindow.close();
    }

    if (aboutWindow) {
      aboutWindow.close();
    }
    mainWindow.destroy();
  });

  // Emitted when the window is closed.
  mainWindow.on('closed', () => {
    mainWindow = null
  });
}

let terminalWindow

function createTerminalWindow() {
  // Create the browser window.
  terminalWindow = new BrowserWindow({
    width: 512,
    height: 256,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath
  })
  terminalWindow.removeMenu();
  terminalWindow.setMinimumSize(300, 150);
  terminalWindow.loadURL('http://localhost:8000/templates/terminal.html');

  terminalWindow.on('closed', () => {
    terminalWindow = null;
  });
}

let viewWindow;
let pendingViewMessage = null;

function createViewWindow(windowName) {
  // Create the browser window.
  viewWindow = new BrowserWindow({
    title: `Viewing ${windowName}`,
    width: 800,
    height: 1024,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath,
    show: false
  })

  viewWindow.setMinimumSize(800, 1024);
  viewWindow.removeMenu();
  viewWindow.loadURL('http://localhost:8000/templates/view.html');

  viewWindow.on('closed', () => {
    viewWindow = null
  })

  viewWindow.webContents.on('did-finish-load', function () {
    viewWindow.show();

    if (pendingViewMessage) {
      setTimeout(() => {
        viewWindow.webContents.send('receive-message', pendingViewMessage);
        pendingViewMessage = null;
      }, 500);
    }
  });

}

let aboutWindow;

function createAboutWindow(data) {
  aboutWindow = new BrowserWindow({
    title: 'About',
    width: 800,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath,
    show: false
  })

  aboutWindow.setMinimumSize(500, 600);
  aboutWindow.removeMenu();

  // Load HTML directly using data URL
  aboutWindow.loadURL('http://localhost:8000/templates/about.html');

  aboutWindow.on('closed', () => {
    aboutWindow = null
  })

  aboutWindow.webContents.on('did-finish-load', () => {
    aboutWindow.webContents.send('about-data', {
      version: data.version,
      electronVersion: process.versions.electron,
      nodeVersion: process.versions.node,
      chromiumVersion: process.versions.chrome,
      license_key: data.license_key,
      activated: data.activated,
      feature: data.feature,
      days_remaining: data.days_remaining
    });
    aboutWindow.show();
  });
}

ipcMain.on('open-about-window', (event, data) => {
  if (!viewWindow) {
    createAboutWindow(data);
  }
})

ipcMain.on('message-to-view', (event, data) => {
  pendingViewMessage = data;

  if (viewWindow) {
    viewWindow.webContents.send('receive-message', data)
  }
})

ipcMain.on('message-to-main', (event, data) => {
  if (mainWindow) {
    mainWindow.webContents.send('receive-message', data)
  }
})

ipcMain.on('open-view-window', (event, data) => {
  if (!viewWindow) {
    createViewWindow(data);
  }
})

ipcMain.handle('show-directory-dialog', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory']
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.on('focus-fix', () => {
  mainWindow.blur();
  mainWindow.focus();
});

const menuTemplate = [
  {
    label: 'File',
    submenu: [
      {
        label: 'Change Output Directory',
        click: async () => {
          const path = await dialog.showOpenDialog({
            properties: ['openDirectory']
          });
          if (!path.canceled) {
            mainWindow.webContents.send('directory-selected', path.filePaths[0]);
          }
        }
      },
      { role: 'quit' },
    ],
  },
  {
    label: 'Edit',
    submenu: [
      { role: 'undo' },
      { role: 'redo' },
      { type: 'separator' },
      { role: 'cut' },
      { role: 'copy' },
      { role: 'paste' },
    ],
  },
  {
    label: 'View',
    submenu: [
      { role: 'toggledevtools' },
      { type: 'separator' },
      { role: 'resetzoom' },
      { role: 'zoomin' },
      { role: 'zoomout' },
      { type: 'separator' },
      { role: 'togglefullscreen' },
    ],
  },
  {
    label: 'Tools',
    submenu: [
      {
        label: 'Terminal',
        click() {
          createTerminalWindow();
        },
      },
    ],
  },
  {
    label: 'Help',
    submenu: [
      {
        label: 'Learn More',
        click() {
          require('electron').shell.openExternal('https://s2aulendo.github.io/HeatCompensation-Docs/');
        },
      },
      {
        label: 'Upgrade',
        click() {
          require('electron').shell.openExternal('https://ulendo.webflow.io/pricinghc');
        },
      },
      {
        label: 'Enter new key',
        click() {
          mainWindow.webContents.send('enter-new-key');
        },
      },
      {
        label: 'About app',
        click: async () => {
          mainWindow.webContents.send('get-app-info');
        }
      }
    ],
  },
];

const menu = Menu.buildFromTemplate(menuTemplate);
Menu.setApplicationMenu(menu);

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow)

// Quit when all windows are closed.
app.on('window-all-closed', function () {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', function () {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) createWindow()
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.

// disable refreshing
app.on('browser-window-focus', function () {
  globalShortcut.register("CommandOrControl+R", () => {
    console.log("CommandOrControl+R is pressed: Shortcut Disabled");
  });
  globalShortcut.register("F5", () => {
    console.log("F5 is pressed: Shortcut Disabled");
  });
  globalShortcut.register("F1", () => {
    require('electron').shell.openExternal('https://s2aulendo.github.io/HeatCompensation-Docs/');
  });
});

app.on('browser-window-blur', function () {
  globalShortcut.unregister('CommandOrControl+R');
  globalShortcut.unregister('F5');
  globalShortcut.unregister('F1');
});