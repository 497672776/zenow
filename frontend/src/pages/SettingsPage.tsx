import { useState, useEffect } from 'react'
import './SettingsPage.css'
import { getBackendBaseUrl } from '../utils/backendPort'
import ModelSection from '../components/ModelSection'

let API_BASE_URL = 'http://localhost:8050' // Default fallback

interface DefaultDownloadUrls {
  urls: { [key: string]: string[] }
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
  const [paramMessage, setParamMessage] = useState('')

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

  useEffect(() => {
    // Initialize backend URL
    getBackendBaseUrl().then(url => {
      API_BASE_URL = url
      console.log('Using backend URL:', API_BASE_URL)
    })

    fetchParameters()
  }, [])

  const fetchParameters = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models/get_param?mode=llm`)
      const data: LLMParameters = await response.json()
      setParameters(data)
    } catch (error) {
      console.error('Failed to fetch parameters:', error)
    }
  }

  const handleApplyParameters = async () => {
    try {
      setParamMessage('正在应用参数...')

      const response = await fetch(`${API_BASE_URL}/api/models/update_param?mode=llm`, {
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

  return (
    <div className="settings-page">
      <div className="settings-content">
        {/* Three Model Sections Side-by-Side */}
        <div className="model-sections-container">
          <ModelSection
            mode="llm"
            title="LLM 模型"
            apiBaseUrl={API_BASE_URL}
          />
          <ModelSection
            mode="embed"
            title="Embed 模型"
            apiBaseUrl={API_BASE_URL}
          />
          <ModelSection
            mode="rerank"
            title="Rerank 模型"
            apiBaseUrl={API_BASE_URL}
          />
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
