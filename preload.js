
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld(
    'electronAPI', {
    // Expose the function to open new window
    selectDirectory: () => ipcRenderer.invoke('show-directory-dialog'),
    focus: () => ipcRenderer.send('focus-fix'),
    getAppInfo: (callback) => {
        ipcRenderer.on('get-app-info', () => callback());
    },
    checkMpRunning: (callback) => {
        ipcRenderer.on('check-mp-running', () => callback());
    },
    enterNewKey: (callback) => {
        ipcRenderer.on('enter-new-key', () => callback());
    },
    onDirectorySelected: (callback) => {
        ipcRenderer.on('directory-selected', (_, path) => callback(path));
    },
    onSelectFile: () => ipcRenderer.invoke('open-file'),
    openViewWindow: (windowName) => ipcRenderer.send('open-view-window', windowName),
    openAboutWindow: (data) => ipcRenderer.send('open-about-window', data),
    mpRunningResponse: (data) => ipcRenderer.send('mp-running-response', data),
    onAboutData: (callback) => ipcRenderer.on('about-data', (event, data) => callback(data)), // to get data across a callback
    sendToView: (data) => ipcRenderer.send('message-to-view', data),
    sendToMain: (data) => ipcRenderer.send('message-to-main', data),
    onReceiveMessage: (callback) => ipcRenderer.on('receive-message', (event, data) => callback(data)),
    displayError: (status, message) => ipcRenderer.send('display-error', status, message),
    // Other API methods you might need
    minimize: () => ipcRenderer.send('minimize-window'),
    maximize: () => ipcRenderer.send('maximize-window')
}
)