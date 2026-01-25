import { contextBridge, ipcRenderer } from 'electron'

// Forward console.log to main process so it appears in terminal
const originalConsoleLog = console.log
const originalConsoleWarn = console.warn
const originalConsoleError = console.error

console.log = (...args: any[]) => {
  originalConsoleLog(...args)
  ipcRenderer.send('log', ['log', ...args])
}

console.warn = (...args: any[]) => {
  originalConsoleWarn(...args)
  ipcRenderer.send('log', ['warn', ...args])
}

console.error = (...args: any[]) => {
  originalConsoleError(...args)
  ipcRenderer.send('log', ['error', ...args])
}

contextBridge.exposeInMainWorld('electronAPI', {
  // Add any APIs you need to expose from main process to renderer
  send: (channel: string, data: any) => {
    ipcRenderer.send(channel, data)
  },
  on: (channel: string, func: (...args: any[]) => void) => {
    ipcRenderer.on(channel, (_event, ...args) => func(_event, ...args))
  },
  removeListener: (channel: string, func: (...args: any[]) => void) => {
    ipcRenderer.removeListener(channel, func)
  },
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  readPortFile: () => ipcRenderer.invoke('read-port-file'),
  checkProcessRunning: (pid: number) => ipcRenderer.invoke('check-process-running', pid),
})
