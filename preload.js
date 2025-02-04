
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld(
    'electronAPI', {
    // Expose the function to open new window
    selectDirectory: () => ipcRenderer.invoke('show-directory-dialog'),
    getAppInfo: (callback) => {
        ipcRenderer.on('get-app-info', () => callback());
    },
    enterNewKey: (callback) => {
        ipcRenderer.on('enter-new-key', () => callback());
    },
    onDirectorySelected: (callback) => {
        ipcRenderer.on('directory-selected', (_, path) => callback(path));
    },
    openViewWindow: (windowName) => ipcRenderer.send('open-view-window', windowName),
    openAboutWindow: (data) => ipcRenderer.send('open-about-window', data),
    onAboutData: (callback) => ipcRenderer.on('about-data', (event, data) => callback(data)), // to get data across a callback
    sendToView: (data) => ipcRenderer.send('message-to-view', data),
    sendToMain: (data) => ipcRenderer.send('message-to-main', data),
    onReceiveMessage: (callback) => ipcRenderer.on('receive-message', (event, data) => callback(data)),
    // Other API methods you might need
    minimize: () => ipcRenderer.send('minimize-window'),
    maximize: () => ipcRenderer.send('maximize-window')
}
)