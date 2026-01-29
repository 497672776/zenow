import React, { useState } from 'react'
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[500px] max-h-[600px] overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">上传文档</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={uploading}
          >
            ✕
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">
              上传到知识库: <span className="font-medium">{kbName}</span>
            </p>
          </div>

          {/* 文件选择 */}
          <div className="mb-6">
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              disabled={uploading}
            />
            <p className="text-xs text-gray-500 mt-2">
              支持 PDF、Word、文本文件等格式
            </p>
          </div>

          {/* 选中的文件列表 */}
          {selectedFiles.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                已选择 {selectedFiles.length} 个文件:
              </h4>
              <div className="max-h-32 overflow-y-auto space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <span className="text-gray-700 truncate">{file.name}</span>
                    <span className="text-gray-500 ml-2">{formatFileSize(file.size)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 上传进度 */}
          {uploading && (
            <div className="mb-6">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-700">上传进度</span>
                <span className="text-gray-500">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            disabled={uploading}
          >
            取消
          </button>
          <button
            onClick={handleUpload}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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