import { useState } from 'react'
import './FileUploadDialog.css'

interface FileUploadDialogProps {
  kbName: string
  onSuccess: () => void
  onClose: () => void
}

const FileUploadDialog: React.FC<FileUploadDialogProps> = ({
  kbName,
  onSuccess,
  onClose,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setSelectedFiles(files)
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    setUploadProgress(0)

    try {
      // TODO: 替换为实际的上传逻辑
      // 模拟上传进度
      for (let i = 0; i <= 100; i += 10) {
        setUploadProgress(i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      console.log(`上传 ${selectedFiles.length} 个文件到知识库 ${kbName}`)
      onSuccess()
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="file-upload-dialog-overlay">
      <div className="file-upload-dialog">
        {/* 头部 */}
        <div className="file-upload-header">
          <h3 className="file-upload-title">上传文档</h3>
          <button
            onClick={onClose}
            className="file-upload-close"
            disabled={uploading}
          >
            ✕
          </button>
        </div>

        {/* 内容 */}
        <div className="file-upload-content">
          <div className="file-upload-kb-name">
            上传到知识库: <strong>{kbName}</strong>
          </div>

          {/* 文件选择 */}
          <div className="file-upload-input-group">
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={handleFileSelect}
              className="file-upload-input"
              disabled={uploading}
            />
            <p className="file-upload-hint">
              支持 PDF、Word、文本文件等格式
            </p>
          </div>

          {/* 选中的文件列表 */}
          {selectedFiles.length > 0 && (
            <div className="file-upload-list">
              <h4 className="file-upload-list-title">
                已选择 {selectedFiles.length} 个文件:
              </h4>
              <div className="file-upload-list-items">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-upload-list-item">
                    <span className="file-upload-list-item-name">{file.name}</span>
                    <span className="file-upload-list-item-size">{formatFileSize(file.size)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 上传进度 */}
          {uploading && (
            <div className="file-upload-progress">
              <div className="file-upload-progress-label">
                <span>上传进度</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="file-upload-progress-bar">
                <div
                  className="file-upload-progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="file-upload-footer">
          <button
            onClick={onClose}
            className="file-upload-button cancel"
            disabled={uploading}
          >
            取消
          </button>
          <button
            onClick={handleUpload}
            className="file-upload-button submit"
            disabled={selectedFiles.length === 0 || uploading}
          >
            {uploading ? '上传中...' : '开始上传'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default FileUploadDialog