// preload.js - Place this file in frontend/public/preload.js
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // Example: Send a message to the main process
    sendMessage: (channel, data) => {
        // Whitelist channels
        const validChannels = ['toMain', 'request-data'];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },

    // Example: Receive a message from the main process
    receiveMessage: (channel, func) => {
        const validChannels = ['fromMain', 'response-data'];
        if (validChannels.includes(channel)) {
            // Deliberately strip event as it includes `sender`
            ipcRenderer.on(channel, (event, ...args) => func(...args));
        }
    },

    // Example: Invoke a method in the main process and wait for result
    invoke: (channel, data) => {
        const validChannels = ['get-app-version', 'check-backend-status'];
        if (validChannels.includes(channel)) {
            return ipcRenderer.invoke(channel, data);
        }
    },

    // Platform information
    platform: process.platform,

    // App version (you can set this from package.json)
    appVersion: process.env.npm_package_version || '0.1.0'
});

console.log('Preload script loaded successfully');