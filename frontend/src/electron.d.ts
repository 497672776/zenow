export interface IElectronAPI {
  send: (channel: string, data: any) => void
  on: (channel: string, func: (...args: any[]) => void) => void
  openFileDialog: () => Promise<string | null>
  readPortFile: () => Promise<string | null>
  checkProcessRunning: (pid: number) => Promise<boolean>
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
