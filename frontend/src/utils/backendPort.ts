/**
 * Utility to read backend port from config file
 */

const DEFAULT_PORT = 8050

/**
 * Read backend port from the port file written by backend
 * Falls back to default port if file doesn't exist or can't be read
 */
export async function getBackendPort(): Promise<number> {
  try {
    const portFile = await window.electronAPI.readPortFile()
    if (portFile) {
      const lines = portFile.trim().split('\n')
      if (lines.length >= 2) {
        const port = parseInt(lines[0], 10)
        const pid = parseInt(lines[1], 10)

        if (!isNaN(port) && !isNaN(pid)) {
          // Verify process is still running
          const isRunning = await window.electronAPI.checkProcessRunning(pid)
          if (isRunning) {
            console.log(`✅ Found backend at port ${port} (PID: ${pid})`)
            return port
          } else {
            console.warn(`⚠️ Backend PID ${pid} not running, using default port`)
          }
        }
      }
    }
  } catch (error) {
    console.warn('Failed to read backend port file, using default:', error)
  }

  console.log(`Using default backend port: ${DEFAULT_PORT}`)
  return DEFAULT_PORT
}

/**
 * Get backend base URL
 */
export async function getBackendBaseUrl(): Promise<string> {
  const port = await getBackendPort()
  return `http://localhost:${port}`
}
