import { useState, useEffect } from 'react'
import './SettingsPage.css'
import { getBackendBaseUrl } from '../utils/backendPort'
import ModelDropdown from '../components/ModelDropdown'

let API_BASE_URL = 'http://localhost:8050' // Default fallback

interface ModelInfo {
  id: number
  name: string
  path: string
  status: string
  is_downloaded: boolean
}

interface ModelListResponse {
  models: ModelInfo[]
  current_model: ModelInfo | null
}

interface ServerStatus {
  status: string
  model_name: string | null
  model_path: string | null
  is_running: boolean
  error_message: string | null
}

interface DefaultDownloadUrls {
  urls: string[]
  browser_path: string
}

interface LLMParameters {
  // LLMServer 参数
  context_size: number
  threads: number
  gpu_layers: number
  batch_size: number
  // LLMClient 参数
  temperature: number
  repeat_penalty: number
  max_tokens: number
}

function SettingsPage() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [currentModel, setCurrentModel] = useState<ModelInfo | null>(null)
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null)
  const [message, setMessage] = useState('')

  // Download state
  const [defaultUrls, setDefaultUrls] = useState<string[]>([])

  // LLM Parameters state
  const [parameters, setParameters] = useState<LLMParameters>({
    context_size: 15360,
    threads: 8,
    gpu_layers: 0,
    batch_size: 512,
    temperature: 0.7,
    repeat_penalty: 1.1,
    max_tokens: 2048
  })
  const [paramMessage, setParamMessage] = useState('')

  useEffect(() => {
    // Initialize backend URL
    getBackendBaseUrl().then(url => {
      API_BASE_URL = url
      console.log('Using backend URL:', API_BASE_URL)
    })

    fetchModels()
    fetchServerStatus()
    fetchDefaultUrls()
    fetchParameters()

    // Poll server status every 2 seconds
    const interval = setInterval(fetchServerStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`)
      const data: ModelListResponse = await response.json()
      setModels(data.models)
      setCurrentModel(data.current_model)
    } catch (error) {
      console.error('Failed to fetch models:', error)
      setMessage('Failed to load models')
    }
  }

  const fetchServerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/server/status`)
      const data: ServerStatus = await response.json()
      setServerStatus(data)
    } catch (error) {
      console.error('Failed to fetch server status:', error)
    }
  }

  const fetchDefaultUrls = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/downloads/default-urls`)
      const data: DefaultDownloadUrls = await response.json()
      setDefaultUrls(data.urls)
    } catch (error) {
      console.error('Failed to fetch default URLs:', error)
    }
  }

  const fetchParameters = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/parameters`)
      const data: LLMParameters = await response.json()
      setParameters(data)
    } catch (error) {
      console.error('Failed to fetch parameters:', error)
    }
  }

  const handleApplyParameters = async () => {
    try {
      setParamMessage('正在应用参数...')

      const response = await fetch(`${API_BASE_URL}/api/parameters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(parameters),
      })

      const result = await response.json()

      if (result.success) {
        setParamMessage(result.message)
        await fetchParameters()
        setTimeout(() => setParamMessage(''), 5000)
      } else {
        setParamMessage(`失败: ${result.message}`)
      }
    } catch (error) {
      console.error('Failed to apply parameters:', error)
      setParamMessage('参数应用失败')
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

  const handleSelectModel = async (modelName: string, downloadUrl?: string) => {
    try {
      setMessage(downloadUrl ? '正在下载并激活模型...' : '正在切换模型...')

      const response = await fetch(`${API_BASE_URL}/api/models/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: modelName,
          download_url: downloadUrl
        }),
      })

      const result = await response.json()

      if (result.success) {
        setMessage(result.message)
        await fetchModels()
        await fetchServerStatus()
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage(`失败: ${result.message}`)
      }
    } catch (error) {
      console.error('Failed to select model:', error)
      setMessage('模型选择失败')
    }
  }

  return (
    <div className="settings-page">
      <div className="settings-content">
        {/* LLM Model Management Section - 合并服务器状态和模型管理 */}
        <div className="setting-section">

          {/* Model Selector with inline status */}
          <div className="model-selector-with-status">
            <div className="model-label-row">
              <span className="model-label">LLM模型</span>
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
              // Select model (already downloaded)
              handleSelectModel(modelName)
            }}
            onDownload={(modelName) => {
              // Find URL for this model and download + activate
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
            label=""
            showDownloadProgress={false}
            downloadProgress={0}
          />
          </div>

          {/* Message Display */}
          {message && (
            <div className={`message ${message.includes('失败') || message.includes('错误') ? 'error' : 'success'}`}>
              {message}
            </div>
          )}
        </div>

        {/* LLM Parameters Configuration Section */}
        <div className="setting-section">
          <h2>LLM 参数配置</h2>

          <div className="param-group">
            <h3>服务器参数（修改后需重启）</h3>

            <div className="param-row">
              <label>上下文窗口大小 (context_size):</label>
              <input
                type="number"
                value={parameters.context_size}
                onChange={(e) => setParameters({...parameters, context_size: parseInt(e.target.value)})}
                min="512"
                max="131072"
              />
            </div>

            <div className="param-row">
              <label>CPU 线程数 (threads):</label>
              <input
                type="number"
                value={parameters.threads}
                onChange={(e) => setParameters({...parameters, threads: parseInt(e.target.value)})}
                min="1"
                max="64"
              />
            </div>

            <div className="param-row">
              <label>GPU 层数 (gpu_layers):</label>
              <input
                type="number"
                value={parameters.gpu_layers}
                onChange={(e) => setParameters({...parameters, gpu_layers: parseInt(e.target.value)})}
                min="0"
                max="100"
              />
            </div>

            <div className="param-row">
              <label>批处理大小 (batch_size):</label>
              <input
                type="number"
                value={parameters.batch_size}
                onChange={(e) => setParameters({...parameters, batch_size: parseInt(e.target.value)})}
                min="128"
                max="2048"
              />
            </div>
          </div>

          <div className="param-group">
            <h3>客户端参数（立即生效）</h3>

            <div className="param-row">
              <label>采样温度 (temperature):</label>
              <input
                type="number"
                step="0.1"
                value={parameters.temperature}
                onChange={(e) => setParameters({...parameters, temperature: parseFloat(e.target.value)})}
                min="0"
                max="2"
              />
            </div>

            <div className="param-row">
              <label>重复惩罚 (repeat_penalty):</label>
              <input
                type="number"
                step="0.1"
                value={parameters.repeat_penalty}
                onChange={(e) => setParameters({...parameters, repeat_penalty: parseFloat(e.target.value)})}
                min="0"
                max="2"
              />
            </div>

            <div className="param-row">
              <label>最大 Token 数 (max_tokens):</label>
              <input
                type="number"
                value={parameters.max_tokens}
                onChange={(e) => setParameters({...parameters, max_tokens: parseInt(e.target.value)})}
                min="128"
                max="8192"
              />
            </div>
          </div>

          <button className="apply-button" onClick={handleApplyParameters}>
            应用参数
          </button>

          {/* Parameter Message Display */}
          {paramMessage && (
            <div className={`message ${paramMessage.includes('失败') || paramMessage.includes('错误') ? 'error' : 'success'}`}>
              {paramMessage}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default SettingsPage
