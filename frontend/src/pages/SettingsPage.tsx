import { useState, useEffect } from 'react'
import './SettingsPage.css'

const API_BASE_URL = 'http://localhost:8000'

interface ModelInfo {
  id: number
  name: string
  path: string
  status: string
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

function SettingsPage() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [currentModel, setCurrentModel] = useState<ModelInfo | null>(null)
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')

  // Add model form state
  const [showAddForm, setShowAddForm] = useState(false)
  const [newModelName, setNewModelName] = useState('')
  const [newModelPath, setNewModelPath] = useState('')
  const [inputType, setInputType] = useState<'path' | 'url'>('path')

  useEffect(() => {
    fetchModels()
    fetchServerStatus()

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

  const handleAddModel = async () => {
    if (!newModelName.trim() || !newModelPath.trim()) {
      setMessage('Please fill in all fields')
      return
    }

    setIsLoading(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/models/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newModelName,
          path: newModelPath,
        }),
      })

      if (response.ok) {
        setMessage('Model added successfully!')
        setNewModelName('')
        setNewModelPath('')
        setShowAddForm(false)
        await fetchModels()
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage('Failed to add model')
      }
    } catch (error) {
      console.error('Failed to add model:', error)
      setMessage('Failed to add model')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBrowseFile = async () => {
    try {
      const filePath = await window.electronAPI.openFileDialog()
      if (filePath) {
        setNewModelPath(filePath)
      }
    } catch (error) {
      console.error('Failed to open file dialog:', error)
      setMessage('Failed to open file dialog')
    }
  }

  const handleSetCurrentModel = async (modelId: number) => {
    setIsLoading(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/models/current?model_id=${modelId}`, {
        method: 'POST',
      })

      if (response.ok) {
        setMessage('Current model updated!')
        await fetchModels()
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage('Failed to update current model')
      }
    } catch (error) {
      console.error('Failed to update current model:', error)
      setMessage('Failed to update current model')
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartServer = async () => {
    if (!currentModel) {
      setMessage('Please select a model first')
      return
    }

    setIsLoading(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/server/start`, {
        method: 'POST',
      })

      if (response.ok) {
        setMessage('Server starting...')
        await fetchServerStatus()
        setTimeout(() => setMessage(''), 3000)
      } else {
        const data = await response.json()
        setMessage(`Failed to start server: ${data.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to start server:', error)
      setMessage('Failed to start server')
    } finally {
      setIsLoading(false)
    }
  }

  const handleStopServer = async () => {
    setIsLoading(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/server/stop`, {
        method: 'POST',
      })

      if (response.ok) {
        setMessage('Server stopped')
        await fetchServerStatus()
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage('Failed to stop server')
      }
    } catch (error) {
      console.error('Failed to stop server:', error)
      setMessage('Failed to stop server')
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string, isRunning: boolean) => {
    if (isRunning && status === 'running') return 'green'
    if (status === 'starting') return 'yellow'
    return 'red'
  }

  const getStatusText = (status: string, isRunning: boolean) => {
    if (isRunning && status === 'running') return '已启动'
    if (status === 'starting') return '启动中'
    return '未启动'
  }

  return (
    <div className="settings-page">
      <div className="settings-content">
        {/* Server Status Section */}
        <div className="setting-section">
          <h2>服务器状态</h2>
          {serverStatus && (
            <div className="server-status-info">
              <div className="status-row">
                <span className="status-label">状态:</span>
                <span className="status-indicator">
                  <span
                    className="status-light"
                    style={{ backgroundColor: getStatusColor(serverStatus.status, serverStatus.is_running) }}
                  ></span>
                  {getStatusText(serverStatus.status, serverStatus.is_running)}
                </span>
              </div>
              {serverStatus.model_name && (
                <div className="status-row">
                  <span className="status-label">当前模型:</span>
                  <span>{serverStatus.model_name}</span>
                </div>
              )}
              {serverStatus.error_message && (
                <div className="status-row error">
                  <span className="status-label">错误:</span>
                  <span>{serverStatus.error_message}</span>
                </div>
              )}
              <div className="server-controls">
                <button
                  className="control-button start-button"
                  onClick={handleStartServer}
                  disabled={isLoading || serverStatus.is_running}
                >
                  启动服务器
                </button>
                <button
                  className="control-button stop-button"
                  onClick={handleStopServer}
                  disabled={isLoading || !serverStatus.is_running}
                >
                  停止服务器
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Model Management Section */}
        <div className="setting-section">
          <h2>模型管理</h2>

          <div className="current-model-info">
            <strong>当前模型:</strong>{' '}
            {currentModel ? `${currentModel.name} (ID: ${currentModel.id})` : '未设置'}
          </div>

          <button
            className="add-model-button"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? '取消添加' : '+ 添加模型'}
          </button>

          {showAddForm && (
            <div className="add-model-form">
              <div className="form-group">
                <label>输入类型:</label>
                <div className="radio-group">
                  <label>
                    <input
                      type="radio"
                      value="path"
                      checked={inputType === 'path'}
                      onChange={() => setInputType('path')}
                    />
                    本地路径
                  </label>
                  <label>
                    <input
                      type="radio"
                      value="url"
                      checked={inputType === 'url'}
                      onChange={() => setInputType('url')}
                    />
                    下载链接
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="model-name">模型名称:</label>
                <input
                  id="model-name"
                  type="text"
                  value={newModelName}
                  onChange={(e) => setNewModelName(e.target.value)}
                  placeholder="例如: Qwen2.5-0.5B-Instruct"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="model-path">
                  {inputType === 'path' ? '模型路径:' : '下载链接:'}
                </label>
                <div className="path-input-group">
                  <input
                    id="model-path"
                    type="text"
                    value={newModelPath}
                    onChange={(e) => setNewModelPath(e.target.value)}
                    placeholder={
                      inputType === 'path'
                        ? '例如: /home/user/models/model.gguf'
                        : '例如: https://example.com/model.gguf'
                    }
                    className="form-input"
                  />
                  {inputType === 'path' && (
                    <button
                      type="button"
                      className="browse-button"
                      onClick={handleBrowseFile}
                    >
                      浏览...
                    </button>
                  )}
                </div>
              </div>

              <button
                className="save-button"
                onClick={handleAddModel}
                disabled={isLoading}
              >
                {isLoading ? '添加中...' : '添加模型'}
              </button>
            </div>
          )}

          <div className="models-list">
            <h3>已添加的模型</h3>
            {models.length === 0 ? (
              <p className="no-models">暂无模型，请添加模型</p>
            ) : (
              <table className="models-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>名称</th>
                    <th>路径</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => (
                    <tr key={model.id} className={currentModel?.id === model.id ? 'current-row' : ''}>
                      <td>{model.id}</td>
                      <td>{model.name}</td>
                      <td className="path-cell" title={model.path}>
                        {model.path}
                      </td>
                      <td>
                        <span
                          className="status-light"
                          style={{ backgroundColor: getStatusColor(model.status, serverStatus?.is_running || false) }}
                        ></span>
                        {model.status}
                      </td>
                      <td>
                        <button
                          className="set-current-button"
                          onClick={() => handleSetCurrentModel(model.id)}
                          disabled={isLoading || currentModel?.id === model.id}
                        >
                          {currentModel?.id === model.id ? '当前' : '设为当前'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {message && (
            <div className={`message ${message.includes('success') || message.includes('成功') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}
        </div>

        {/* About Section */}
        <div className="setting-section">
          <h2>关于</h2>
          <p>Zenow Chat - LLM 聊天应用</p>
          <p>版本 0.1.0</p>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
