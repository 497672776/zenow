import { app, BrowserWindow, Menu, ipcMain, dialog } from 'electron'
import path from 'path'
import fs from 'fs'
import os from 'os'

const isDev = process.env.NODE_ENV === 'development'

// Disable certificate verification in development (for localhost SSL errors)
if (isDev) {
  app.commandLine.appendSwitch('ignore-certificate-errors')
}

function createWindow() {
  // Disable application menu
  Menu.setApplicationMenu(null)

  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false, // Hide system title bar
    transparent: true, // Enable transparency for rounded corners
    backgroundColor: '#00000000', // Transparent background
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  // Window control handlers
  ipcMain.on('window-minimize', () => {
    mainWindow.minimize()
  })

  ipcMain.on('window-maximize', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow.maximize()
    }
  })

  ipcMain.on('window-close', () => {
    mainWindow.close()
  })

  // 监听窗口最大化/还原事件，通知渲染进程
  mainWindow.on('maximize', () => {
    mainWindow.webContents.send('window-maximized', true)
  })

  mainWindow.on('unmaximize', () => {
    mainWindow.webContents.send('window-maximized', false)
  })

  // File dialog handler
  ipcMain.handle('dialog:openFile', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile'],
      filters: [
        { name: 'GGUF Models', extensions: ['gguf'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })

    if (!result.canceled && result.filePaths.length > 0) {
      return result.filePaths[0]
    }
    return null
  })

  // Read backend port file
  ipcMain.handle('read-port-file', async () => {
    try {
      const portFile = path.join(os.homedir(), '.config', 'zenow', 'backend.port')
      if (fs.existsSync(portFile)) {
        const content = fs.readFileSync(portFile, 'utf-8')
        return content
      }
    } catch (error) {
      console.error('Failed to read port file:', error)
    }
    return null
  })

  // Check if process is running
  ipcMain.handle('check-process-running', async (_event, pid: number) => {
    try {
      // On Unix-like systems, sending signal 0 checks if process exists
      process.kill(pid, 0)
      return true
    } catch (error) {
      return false
    }
  })

  // Forward renderer console to main process terminal
  ipcMain.on('log', (_event, args) => {
    const [level, ...rest] = args
    const prefix = '[renderer]'

    switch (level) {
      case 'log':
        console.log(prefix, ...rest)
        break
      case 'warn':
        console.warn(prefix, ...rest)
        break
      case 'error':
        console.error(prefix, ...rest)
        break
      default:
        console.log(prefix, ...args)
    }
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    // mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  // Add keyboard shortcut to toggle DevTools (F12 or Ctrl+Shift+I)
  mainWindow.webContents.on('before-input-event', (_event, input) => {
    if (input.key === 'F12' ||
        (input.control && input.shift && input.key.toLowerCase() === 'i')) {
      mainWindow.webContents.toggleDevTools()
    }
  })
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
