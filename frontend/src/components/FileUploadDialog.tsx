import { useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import './FileUploadDialog.css'

interface FileUploadDialogProps {
  kbName: string
  onSuccess: () => void
  onClose: () => void
}

type FileStatus = 'pending' | 'uploading' | 'completed' | 'failed'

interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  status: FileStatus
  progress: number
  error?: string
}

const FileUploadDialog: React.FC<FileUploadDialogProps> = ({
  kbName,
  onSuccess,
  onClose,
}) => {
  const [dragging, setDragging] = useState(false)
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 获取文件扩展名
  const getFileExtension = (fileName: string): string => {
    const ext = fileName.split('.').pop()?.toUpperCase()
    return ext || 'FILE'
  }

  // 拖拽事件处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    addFiles(files)
  }

  // 文件选择
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    addFiles(files)
  }

  // 添加文件到列表
  const addFiles = (files: File[]) => {
    const newUploadFiles: UploadFile[] = files.map(file => ({
      id: `file-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      name: file.name,
      size: file.size,
      status: 'pending' as FileStatus,
      progress: 0
    }))

    if (newUploadFiles.length > 0) {
      setUploadFiles(prev => [...prev, ...newUploadFiles])
    }

    // 清空 input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 开始上传
  const handleUpload = async () => {
    if (uploadFiles.length === 0) return

    // 模拟上传
    for (const uploadFile of uploadFiles) {
      if (uploadFile.status !== 'pending') continue

      // 更新为上传中
      setUploadFiles(prev => prev.map(f =>
        f.id === uploadFile.id ? { ...f, status: 'uploading' as FileStatus } : f
      ))

      // 模拟上传进度
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 100))
        setUploadFiles(prev => prev.map(f =>
          f.id === uploadFile.id ? { ...f, progress: i } : f
        ))
      }

      // 更新为完成
      setUploadFiles(prev => prev.map(f =>
        f.id === uploadFile.id ? { ...f, status: 'completed' as FileStatus, progress: 100 } : f
      ))
    }

    // 所有文件上传完成
    setTimeout(() => {
      onSuccess()
      onClose()
    }, 500)
  }

  // 删除文件
  const removeFile = (fileId: string) => {
    setUploadFiles(prev => prev.filter(f => f.id !== fileId))
  }

  // 渲染文件状态
  const renderFileStatus = (file: UploadFile) => {
    switch (file.status) {
      case 'pending':
        return <span className="file-status pending">等待中</span>
      case 'uploading':
        return (
          <>
            <span className="file-status uploading">{file.progress}%</span>
            <div className="spinner" />
          </>
        )
      case 'completed':
        return (
          <>
            <span className="file-status completed">已上传</span>
            <svg className="status-icon success" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M11.667 3.5L5.25 9.917L2.333 7" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </>
        )
      case 'failed':
        return (
          <>
            <span className="file-status failed">上传失败</span>
            <svg className="status-icon error" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5" stroke="#EF4444" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </>
        )
    }
  }

  return createPortal(
    <div className="file-upload-dialog-overlay" onClick={onClose}>
      <div className="file-upload-dialog" onClick={(e) => e.stopPropagation()}>
        {/* 头部 */}
        <div className="file-upload-header">
          <h3 className="file-upload-title">上传文档</h3>
          <button
            onClick={onClose}
            className="file-upload-close"
            disabled={uploadFiles.some(f => f.status === 'uploading')}
          >
            ✕
          </button>
        </div>

        {/* 拖拽上传区 */}
        <div
          className={`drop-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="drop-zone-content">
            <p className="drop-zone-title">拖拽文件到这里上传</p>
            <p className="drop-zone-subtitle">
              支持 PDF、Word、Excel、PPT、TXT、MD 等格式<br />
              每个文件最大 250MB
            </p>
            <div className="select-buttons-group">
              <button
                className="select-file-button"
                onClick={() => fileInputRef.current?.click()}
              >
                选择文件
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md,.xls,.xlsx,.ppt,.pptx"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
            />
          </div>
        </div>

        {/* 文件列表 */}
        {uploadFiles.length > 0 && (
          <div className="file-list-section">
            <h4 className="section-title">已选择 {uploadFiles.length} 个文件</h4>
            <div className="file-list">
              {uploadFiles.map((file) => (
                <div key={file.id} className={`file-item ${file.status}`}>
                  {/* 文件图标 */}
                  <div className="file-icon">
                    {getFileExtension(file.name).slice(0, 3)}
                  </div>

                  {/* 文件信息 */}
                  <div className="file-info">
                    <div className="file-name" title={file.name}>{file.name}</div>
                    <div className="file-details">
                      <span className="file-size">{formatFileSize(file.size)}</span>
                      {renderFileStatus(file)}
                    </div>
                    {file.status === 'uploading' && (
                      <div className="file-progress">
                        <div className="file-progress-fill" style={{ width: `${file.progress}%` }} />
                      </div>
                    )}
                  </div>

                  {/* 删除按钮 */}
                  {file.status !== 'uploading' && (
                    <button
                      className="delete-button"
                      onClick={() => removeFile(file.id)}
                      aria-label={`删除 ${file.name}`}
                    >
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M2.5 5H17.5M8.333 9.167V14.167M11.667 9.167V14.167M3.333 5L4.167 16.667C4.167 17.108 4.342 17.531 4.654 17.843C4.966 18.155 5.39 18.333 5.833 18.333H14.167C14.61 18.333 15.033 18.155 15.345 17.843C15.657 17.531 15.833 17.108 15.833 16.667L16.667 5M7.5 5V3.333C7.5 3.113 7.588 2.901 7.744 2.744C7.901 2.588 8.113 2.5 8.333 2.5H11.667C11.887 2.5 12.099 2.588 12.256 2.744C12.412 2.901 12.5 3.113 12.5 3.333V5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 底部按钮 */}
        <div className="file-upload-footer">
          <button
            onClick={onClose}
            className="file-upload-button cancel"
            disabled={uploadFiles.some(f => f.status === 'uploading')}
          >
            取消
          </button>
          <button
            onClick={handleUpload}
            className="file-upload-button submit"
            disabled={uploadFiles.length === 0 || uploadFiles.some(f => f.status === 'uploading')}
          >
            {uploadFiles.some(f => f.status === 'uploading') ? '上传中...' : '开始上传'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}

export default FileUploadDialog