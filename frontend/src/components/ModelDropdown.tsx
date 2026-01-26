import { useState } from 'react'
import './ModelDropdown.css'

interface DownloadProgress {
  url: string
  filename: string
  status: 'downloading' | 'completed' | 'failed'
  downloaded: number
  total: number
  progress: number
  error?: string
}

interface ModelDropdownProps {
  models: string[]
  selectedModel: string
  onSelect: (modelName: string) => void
  onDownload: (modelName: string) => void
  isDownloaded: (modelName: string) => boolean
  getDownloadProgress: (modelName: string) => DownloadProgress | null
  label: string
  mode?: string
  hasCurrentModel?: boolean
  isCurrentDownloaded?: boolean
}

function ModelDropdown({
  models,
  selectedModel,
  onSelect,
  onDownload,
  isDownloaded,
  getDownloadProgress,
  label,
  hasCurrentModel = false,
  isCurrentDownloaded = false
}: ModelDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)

  // 根据状态生成显示文本
  const getDisplayText = () => {
    if (!hasCurrentModel) {
      return '选择模型'
    }

    if (selectedModel) {
      if (isCurrentDownloaded) {
        return `${selectedModel} ✓`
      } else {
        return `${selectedModel} (未下载)`
      }
    }

    return '选择模型'
  }

  // 处理模型点击
  const handleModelClick = (model: string) => {
    const progress = getDownloadProgress(model)

    // 如果正在下载，不做任何操作
    if (progress && progress.status === 'downloading') {
      return
    }

    if (isDownloaded(model)) {
      // 已下载：切换模型
      onSelect(model)
      setIsOpen(false)
    } else {
      // 未下载：开始下载
      onDownload(model)
      // 不关闭下拉菜单，让用户看到下载进度
    }
  }

  return (
    <div className="model-dropdown-container">
      <label className="model-dropdown-label">{label}</label>
      <div className="model-dropdown">
        <button
          className="model-dropdown-toggle"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className={`model-dropdown-selected ${!hasCurrentModel ? 'no-model' : ''}`}>
            {getDisplayText()}
          </span>
          <span className="model-dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
        </button>

        {isOpen && (
          <div className="model-dropdown-menu">
            {models.map((model) => {
              const isModelDownloaded = isDownloaded(model)
              const progress = getDownloadProgress(model)
              const isDownloading = progress && progress.status === 'downloading'

              return (
                <div key={model} className="model-dropdown-item">
                  <button
                    className={`model-item-button ${selectedModel === model ? 'selected' : ''}`}
                    onClick={() => handleModelClick(model)}
                    disabled={!!isDownloading}
                  >
                    <span className="model-item-name">{model}</span>

                    {/* 显示状态：已下载 / 下载进度 / 未下载 */}
                    {isDownloading ? (
                      <div className="model-item-progress">
                        <div className="progress-bar-inline">
                          <div
                            className="progress-fill-inline"
                            style={{ width: `${progress.progress}%` }}
                          />
                        </div>
                        <span className="progress-text-inline">{progress.progress.toFixed(1)}%</span>
                      </div>
                    ) : isModelDownloaded ? (
                      <span className="model-item-badge downloaded">已下载</span>
                    ) : (
                      <span className="model-item-badge not-downloaded">点击下载</span>
                    )}
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default ModelDropdown
