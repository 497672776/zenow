export interface IElectronAPI {
  send: (channel: string, data: any) => void
  on: (channel: string, func: (...args: any[]) => void) => void
  openFileDialog: () => Promise<string | null>
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
