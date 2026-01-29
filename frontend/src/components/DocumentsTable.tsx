import React, { useState, useEffect } from 'react'
import './DocumentsTable.css'

interface Document {
  id: string
  name: string
  kb_name: string
  upload_date: string
  chunk_count: number
  file_size: number
}

interface DocumentsTableProps {
  kbId: string
  kbName: string
  refreshCount: number
  onDocumentDeleted?: () => void
}

const DocumentsTable: React.FC<DocumentsTableProps> = ({
  kbId,
  kbName,
  refreshCount,
  onDocumentDeleted,
}) => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [kbId, refreshCount])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      // TODO: 替换为实际的API调用
      const mockDocuments = [
        {
          id: '1',
          name: '示例文档.pdf',
          kb_name: kbName,
          upload_date: new Date().toISOString(),
          chunk_count: 10,
          file_size: 1024000
        }
      ]
      setDocuments(mockDocuments)
    } catch (error) {
      console.error('Failed to load documents:', error)
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN')
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* 头部 */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-semibold text-gray-900">{kbName}</h1>
        <p className="text-sm text-gray-500 mt-1">共 {documents.length} 个文档</p>
      </div>

      {/* 文档列表 */}
      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-gray-400 text-lg mb-2">📄</div>
              <div className="text-gray-500">暂无文档</div>
              <div className="text-gray-400 text-sm mt-1">点击右侧"添加资料"按钮上传文档</div>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                      <span className="text-blue-600 text-sm">📄</span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{doc.name}</div>
                      <div className="text-sm text-gray-500">
                        {formatFileSize(doc.file_size)} • {doc.chunk_count} 个片段 • {formatDate(doc.upload_date)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="删除文档"
                      onClick={() => {
                        // TODO: 实现删除逻辑
                        console.log('删除文档:', doc.id)
                        onDocumentDeleted?.()
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentsTable