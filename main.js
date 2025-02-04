// Modules to control application life and create native browser window
const path = require('path');
const fs = require('fs');

const { app, BrowserWindow, Menu, ipcMain, dialog, globalShortcut } = require('electron')
const iconPath = path.join(__dirname, "web", "public", "icon.ico");
const iconJPG = path.join(__dirname, "web", "public", "ulendo_favi.jpg");
const iconJPGData = fs.readFileSync(iconPath);
const base64Icon = iconJPGData.toString('base64');
const iconSrc = `data:image/jpeg;base64,${base64Icon}`;

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
  mainWindow.on('closed', function () {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    if (terminalWindow) {
      terminalWindow.close();
    }
    
    if (viewWindow) {
      viewWindow.close();
    }
    mainWindow = null
  })
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

function createAboutWindow(data){
  aboutWindow = new BrowserWindow({
    title: 'About',
    width: 800,
    height: 1024,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath,
    show: false
  })

  aboutWindow.removeMenu();
  // Create HTML content as a string
  const htmlContent = `
  <!DOCTYPE html>
  <html>
  <head>
      <meta charset="UTF-8">
      <title>About Ulendo HC</title>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
      <style>
          body {
              font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
              padding: 2rem;
              background: #f8f9fa;
              color: #2c3e50;
          }
          .header {
              display: flex;
              align-items: center;
              margin-bottom: 2rem;
          }
          .app-icon {
              width: 64px;
              height: 64px;
              margin-right: 1.5rem;
          }
          .card {
              background: white;
              border-radius: 12px;
              padding: 1.5rem;
              margin-bottom: 1.5rem;
              box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          }
          .info-grid {
              display: grid;
              grid-template-columns: repeat(2, 1fr);
              gap: 1rem;
          }
          .status-item {
              display: flex;
              align-items: center;
              padding: 0.75rem;
              background: #f8f9fa;
              border-radius: 8px;
          }
          .status-icon {
              font-size: 1.2rem;
              margin-right: 0.75rem;
              width: 28px;
              text-align: center;
          }
          .feature-level {
              display: inline-block;
              padding: 0.25rem 0.75rem;
              background: #e3f2fd;
              border-radius: 20px;
              color: #1976d2;
              font-weight: 500;
          }
          .days-remaining {
              color: #d32f2f;
              font-weight: 500;
          }
          .electron-logo {
              width: 120px;
              opacity: 0.8;
              margin-top: 2rem;
          }
      </style>
  </head>
  <body>
      <div class="header">
          <img src="${iconSrc}" class="app-icon" alt="App Icon">
          <div>
              <h1 style="margin:0; color: #1976d2;">Ulendo HC</h1>
              <p style="margin:0; color: #666;">Heat Compensation System</p>
          </div>
      </div>
  
      <div class="card">
          <h3><i class="fas fa-info-circle"></i> Application Details</h3>
          <div class="info-grid">
              <div class="status-item">
                  <i class="fas fa-code-branch status-icon"></i>
                  Version: ${data['version']}
              </div>
              <div class="status-item">
                  <i class="fab fa-electron status-icon"></i>
                  Electron: ${process.versions.electron}
              </div>
              <div class="status-item">
                  <i class="fab fa-node-js status-icon"></i>
                  Node.js: ${process.versions.node}
              </div>
              <div class="status-item">
                  <i class="fab fa-chrome status-icon"></i>
                  Chromium: ${process.versions.chrome}
              </div>
          </div>
      </div>
  
      <div class="card">
          <h3><i class="fas fa-key status-icon"></i> License Information</h3>
          <div class="info-grid">
              <div class="status-item" style="background: #e8f5e9;">
                  <i class="fas fa-check-circle status-icon" style="color: #43a047;"></i>
                  Status: ${data['activated'] ? "Activated" : "Not Activated"}
              </div>
              <div class="status-item">
                  <i class="fas fa-layer-group status-icon"></i>
                  Feature Level: <span class="feature-level">${data['feature']}</span>
              </div>
              <div class="status-item">
                  <i class="fas fa-clock status-icon"></i>
                  Days Remaining: <span class="days-remaining">${data['days_remaining']}</span>
              </div>
          </div>
      </div>
  
      <div style="text-align: center; margin-top: 2rem;">
          <img src="https://www.electronjs.org/assets/img/logo.svg" class="electron-logo" alt="Electron Logo">
          <p style="color: #666; font-size: 0.9rem;">Built with Electron Framework</p>
      </div>
  </body>
  </html>
  `;
  // Load HTML directly using data URL
  aboutWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`);

  aboutWindow.on('closed', () => {
    aboutWindow = null
  })

  aboutWindow.webContents.on('did-finish-load', function () {
    aboutWindow.show();
    aboutWindow.webContents.send('about-data', data);
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
        click: async() => {
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