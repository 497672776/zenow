import { useState, useEffect } from 'react'
import ModelDropdown from './ModelDropdown'
import './ModelSection.css'

export interface ModelInfo {
  id: number
  name: string
  path: string
  is_downloaded: boolean
  mode: string
}

export interface ServerStatus {
  status: string
  model_name: string | null
  model_path: string | null
  is_running: boolean
  error_message: string | null
}

export interface DownloadProgress {
  url: string
  filename: string
  status: 'downloading' | 'completed' | 'failed'
  downloaded: number
  total: number
  progress: number
  error?: string
}

export interface DownloadTask {
  modelName: string
  url: string
  progress: DownloadProgress | null
}

export interface ModelSectionProps {
  mode: 'llm' | 'embed' | 'rerank'
  title: string
  apiBaseUrl: string
  onMessage?: (message: string) => void
}

function ModelSection({ mode, title, apiBaseUrl, onMessage }: ModelSectionProps) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [currentModel, setCurrentModel] = useState<ModelInfo | null>(null)
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null)
  const [defaultUrls, setDefaultUrls] = useState<string[]>([])
  const [message, setMessage] = useState('')
  // 改为 Map 结构，支持多个下载任务
  const [downloadTasks, setDownloadTasks] = useState<Map<string, DownloadTask>>(new Map())

  useEffect(() => {
    fetchModels()
    fetchServerStatus()
    fetchDefaultUrls()

    // Poll server status every 2 seconds
    const interval = setInterval(fetchServerStatus, 2000)
    return () => clearInterval(interval)
  }, [mode, apiBaseUrl])

  // Poll download progress for all active downloads
  useEffect(() => {
    if (downloadTasks.size === 0) return

    const interval = setInterval(async () => {
      const updatedTasks = new Map(downloadTasks)
      let hasChanges = false

      for (const [url, task] of downloadTasks.entries()) {
        // Skip if already completed or failed
        if (task.progress?.status === 'completed' || task.progress?.status === 'failed') {
          continue
        }

        try {
          const response = await fetch(
            `${apiBaseUrl}/api/models/download/status?url=${encodeURIComponent(url)}`
          )
          const data = await response.json()

          if (data.success && data.download) {
            updatedTasks.set(url, {
              ...task,
              progress: data.download
            })
            hasChanges = true

            // Download completed or failed
            if (data.download.status === 'completed') {
              showMessage(`${task.modelName} 下载完成！`)
              await fetchModels()
              // Remove from tasks after a delay
              setTimeout(() => {
                setDownloadTasks(prev => {
                  const newTasks = new Map(prev)
                  newTasks.delete(url)
                  return newTasks
                })
              }, 2000)
            } else if (data.download.status === 'failed') {
              showMessage(`${task.modelName} 下载失败: ${data.download.error || '未知错误'}`)
              // Remove from tasks after a delay
              setTimeout(() => {
                setDownloadTasks(prev => {
                  const newTasks = new Map(prev)
                  newTasks.delete(url)
                  return newTasks
                })
              }, 3000)
            }
          }
        } catch (error) {
          console.error(`Failed to fetch download progress for ${task.modelName}:`, error)
        }
      }

      if (hasChanges) {
        setDownloadTasks(updatedTasks)
      }
    }, 1000) // Poll every second

    return () => clearInterval(interval)
  }, [downloadTasks, apiBaseUrl])

  const fetchModels = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/models/list?mode=${mode}`)
      const data = await response.json()
      setModels(data.models || [])
      setCurrentModel(data.current_model || null)
    } catch (error) {
      console.error(`Failed to fetch ${mode} models:`, error)
      showMessage('Failed to load models')
    }
  }

  const fetchServerStatus = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/server/status?mode=${mode}`)
      const data: ServerStatus = await response.json()
      setServerStatus(data)
    } catch (error) {
      console.error(`Failed to fetch ${mode} server status:`, error)
    }
  }

  const fetchDefaultUrls = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/downloads/default-urls`)
      const data = await response.json()
      // data.urls is now a dict by mode
      setDefaultUrls(data.urls[mode] || [])
    } catch (error) {
      console.error(`Failed to fetch default URLs for ${mode}:`, error)
    }
  }

  const showMessage = (msg: string) => {
    setMessage(msg)
    if (onMessage) onMessage(msg)
    setTimeout(() => setMessage(''), 3000)
  }

  const handleSelectModel = async (modelName: string, downloadUrl?: string) => {
    try {
      if (downloadUrl) {
        // Start download and track progress
        showMessage(`开始下载 ${modelName}...`)

        // Add to download tasks
        setDownloadTasks(prev => {
          const newTasks = new Map(prev)
          newTasks.set(downloadUrl, {
            modelName,
            url: downloadUrl,
            progress: null
          })
          return newTasks
        })
      } else {
        showMessage('正在切换模型...')
      }

      const response = await fetch(`${apiBaseUrl}/api/models/load`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: modelName,
          download_url: downloadUrl,
          mode: mode
        }),
      })

      const result = await response.json()

      if (result.success) {
        if (!downloadUrl) {
          // Only show success message if not downloading (download completion will show its own message)
          showMessage(result.message)
        }
        await fetchModels()
        await fetchServerStatus()
      } else {
        showMessage(`失败: ${result.message}`)
        // Remove from download tasks on failure
        if (downloadUrl) {
          setDownloadTasks(prev => {
            const newTasks = new Map(prev)
            newTasks.delete(downloadUrl)
            return newTasks
          })
        }
      }
    } catch (error) {
      console.error(`Failed to select ${mode} model:`, error)
      showMessage('模型选择失败')
      // Remove from download tasks on error
      if (downloadUrl) {
        setDownloadTasks(prev => {
          const newTasks = new Map(prev)
          newTasks.delete(downloadUrl)
          return newTasks
        })
      }
    }
  }

  const getStatusColor = () => {
    if (!serverStatus) return 'red'
    if (serverStatus.is_running && serverStatus.status === 'running') return 'green'
    if (serverStatus.status === 'starting') return 'yellow'
    return 'red'
  }

  const getStatusText = () => {
    if (!serverStatus) return '未启动'
    if (serverStatus.is_running && serverStatus.status === 'running') return '运行中'
    if (serverStatus.status === 'starting') return '启动中'
    return '未启动'
  }

  return (
    <div className="model-section">
      <div className="model-section-header">
        <h3>{title}</h3>
      </div>

      <div className="model-selector-with-status">
        <div className="model-label-row">
          <span className="model-label">当前模型</span>
          <span
            className="status-light-inline"
            style={{ backgroundColor: getStatusColor() }}
          ></span>
          <span className="status-text-inline">{getStatusText()}</span>
        </div>

        <ModelDropdown
          models={Array.from(new Set([
            ...models.map(m => m.name),
            ...defaultUrls.map(url => {
              const filename = url.split('/').pop() || ''
              return filename.replace(/\.gguf$/i, '')
            })
          ]))}
          selectedModel={currentModel?.name || ''}
          onSelect={(modelName) => {
            handleSelectModel(modelName)
          }}
          onDownload={(modelName) => {
            const url = defaultUrls.find(u => {
              const filename = u.split('/').pop() || ''
              return filename.replace(/\.gguf$/i, '') === modelName
            })
            if (url) {
              handleSelectModel(modelName, url)
            }
          }}
          isDownloaded={(modelName) => {
            return models.some(m => m.name === modelName && m.is_downloaded)
          }}
          getDownloadProgress={(modelName) => {
            // Find download task for this model
            for (const task of downloadTasks.values()) {
              if (task.modelName === modelName) {
                return task.progress
              }
            }
            return null
          }}
          label=""
          mode={mode}
          hasCurrentModel={currentModel !== null}
          isCurrentDownloaded={currentModel?.is_downloaded || false}
        />
      </div>

      {message && (
        <div className={`message ${message.includes('失败') || message.includes('错误') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
    </div>
  )
}

export default ModelSection
