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
      if (lines.length >= 1) {
        const port = parseInt(lines[0], 10)
        if (!isNaN(port)) {
          console.log(`📖 Read backend port from file: ${port}`)
          return port
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

/**
 * Check if backend is healthy by calling /api/health
 */
export async function checkBackendHealth(baseUrl?: string): Promise<boolean> {
  try {
    const url = baseUrl || await getBackendBaseUrl()
    const response = await fetch(`${url}/api/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000) // 3 second timeout
    })

    if (!response.ok) {
      return false
    }

    // 验证返回的应用名是否为 zenow
    const data = await response.json()
    if (data.app === 'zenow' && data.status === 'healthy') {
      console.log(`✅ Connected to Zenow backend at ${url}`)
      return true
    } else {
      console.warn(`⚠️ Wrong application at ${url}, expected zenow but got:`, data)
      return false
    }
  } catch (error) {
    console.warn('Backend health check failed:', error)
    return false
  }
}
