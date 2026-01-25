import { useState } from 'react'
import './ModelDropdown.css'

interface ModelDropdownProps {
  models: string[]
  selectedModel: string
  onSelect: (modelName: string) => void
  onDownload: (modelName: string) => void
  isDownloaded: (modelName: string) => boolean
  label: string
  showDownloadProgress?: boolean
  downloadProgress?: number
}

function ModelDropdown({
  models,
  selectedModel,
  onSelect,
  onDownload,
  isDownloaded,
  label,
  showDownloadProgress = false,
  downloadProgress = 0
}: ModelDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="model-dropdown-container">
      <label className="model-dropdown-label">{label}</label>
      <div className="model-dropdown">
        <button
          className="model-dropdown-toggle"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="model-dropdown-selected">{selectedModel || '选择模型'}</span>
          <span className="model-dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
        </button>

        {isOpen && (
          <div className="model-dropdown-menu">
            {models.map((model) => (
              <div key={model} className="model-dropdown-item">
                <button
                  className={`model-item-button ${selectedModel === model ? 'selected' : ''}`}
                  onClick={() => {
                    onSelect(model)
                    setIsOpen(false)
                  }}
                >
                  <span className="model-item-name">{model}</span>
                  {isDownloaded(model) && (
                    <span className="model-item-badge downloaded">已下载</span>
                  )}
                </button>

                {!isDownloaded(model) && (
                  <button
                    className="model-item-download"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDownload(model)
                    }}
                  >
                    ⬇️ 下载
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Download Progress */}
      {showDownloadProgress && downloadProgress > 0 && downloadProgress < 100 && (
        <div className="model-download-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${downloadProgress}%` }}
            />
          </div>
          <span className="progress-text">{downloadProgress.toFixed(1)}%</span>
        </div>
      )}
    </div>
  )
}

export default ModelDropdown
