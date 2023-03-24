// preload.js
const { contextBridge, ipcRenderer } = require('electron');

// Expose the ipcRenderer object to the renderer process
console.log('ipcRenderer: ', ipcRenderer)
contextBridge.exposeInMainWorld('ipcRenderer', ipcRenderer);

// Expose a custom require function that exposes the Node.js require function
contextBridge.exposeInMainWorld('myRequire', {
  require: (moduleName) => require(moduleName),
});


console.log('preload.js loaded');