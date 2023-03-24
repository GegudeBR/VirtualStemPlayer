const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const createWindow = () => {
  const win = new BrowserWindow({
    width: 400,
    height: 350,
    resizable: false, // prevents the window from being resized
    scrollBounce: false, // prevents the window from being scrolled
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  })
  
  win.loadFile('index.html')

  // Open the DevTools deattached from the window
  win.webContents.openDevTools({ mode: 'detach' })
}   


app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Listen for the 'process-file' event from the renderer process
ipcMain.on('process-file', (event, filePath) => {
  console.log('Processing file: ' + filePath)
  // Spawn a new python process
  const pythonProcess = spawn('python3.9', ['./python/main.py', filePath]);

  pythonProcess.on('close', (code) => {
    console.log('Python process exited with code: ' + code);
    const responseName = 'processed-file';
    if (code === 0) {
      event.reply(responseName, 0); // Successfully processed the file
    } else if (code == 1) {
      event.reply(responseName, 1); // Invalid file selected
    } else if (code == 2) {
      event.reply(responseName, 2); // Invalid audio file selected
    } else {
      event.reply(responseName, 3); // Unknown error occurred
    }
  });

  // Monitor the progress of the python process
  pythonProcess.stdout.on('data', (data) => {
    console.log(data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.log(data.toString());
  });

});
