import React, { useState, useEffect } from 'react'
import deleteIcon from '../assets/delete-icon.svg'
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
  const [searchText, setSearchText] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; doc: Document | null }>({
    show: false,
    doc: null,
  })

  useEffect(() => {
    loadDocuments()
  }, [kbId, refreshCount, searchText])

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
        },
        {
          id: '2',
          name: '技术文档.docx',
          kb_name: kbName,
          upload_date: new Date(Date.now() - 86400000).toISOString(),
          chunk_count: 15,
          file_size: 2048000
        }
      ]

      // 过滤搜索结果
      const filtered = searchText
        ? mockDocuments.filter(doc => doc.name.toLowerCase().includes(searchText.toLowerCase()))
        : mockDocuments

      setDocuments(filtered)
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
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}`
  }

  const handleDelete = (doc: Document) => {
    setDeleteConfirm({ show: true, doc })
  }

  const confirmDelete = async () => {
    if (!deleteConfirm.doc) return

    const doc = deleteConfirm.doc
    setDeleteConfirm({ show: false, doc: null })

    try {
      // TODO: 替换为实际的API调用
      console.log('删除文档:', doc.id)
      await new Promise(resolve => setTimeout(resolve, 500))

      await loadDocuments()
      onDocumentDeleted?.()
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除失败')
    }
  }

  const cancelDelete = () => {
    setDeleteConfirm({ show: false, doc: null })
  }

  const getFileIcon = (fileName: string): string => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf':
        return '📄'
      case 'doc':
      case 'docx':
        return '📝'
      case 'xls':
      case 'xlsx':
        return '📊'
      case 'ppt':
      case 'pptx':
        return '📽️'
      case 'txt':
        return '📃'
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return '🖼️'
      default:
        return '📄'
    }
  }

  if (loading) {
    return (
      <div className="documents-table-loading">
        <div className="loading-text">加载中...</div>
      </div>
    )
  }

  return (
    <div className="documents-table">
      {/* 头部 */}
      <div className="documents-table-header">
        <h3 className="documents-table-title">所有资料</h3>
        <div className="documents-table-actions">
          <div className="search-box">
            <svg className="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M7 12C9.76142 12 12 9.76142 12 7C12 4.23858 9.76142 2 7 2C4.23858 2 2 4.23858 2 7C2 9.76142 4.23858 12 7 12Z" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <input
              type="text"
              placeholder="搜索资料文件"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="search-input"
            />
          </div>
          <select className="sort-select">
            <option>排序：最新</option>
            <option>排序：最旧</option>
            <option>排序：文件名</option>
          </select>
        </div>
      </div>

      {/* 表格列头 */}
      <div className="documents-table-columns">
        <div className="column-name">文件名</div>
        <div className="column-date">上传时间</div>
        <div className="column-chunks">分片数</div>
        <div className="column-size">文件大小</div>
        <div className="column-actions">操作</div>
      </div>

      {/* 文档列表 */}
      <div className="documents-table-body">
        {documents.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📄</div>
            <div className="empty-text">暂无文档</div>
            <div className="empty-hint">点击右侧"添加资料"按钮上传文档</div>
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.id} className="document-row">
              <div className="document-name">
                <span className="file-icon">{getFileIcon(doc.name)}</span>
                <span className="file-name" title={doc.name}>{doc.name}</span>
              </div>
              <div className="document-date">{formatDate(doc.upload_date)}</div>
              <div className="document-chunks">{doc.chunk_count}</div>
              <div className="document-size">{formatFileSize(doc.file_size)}</div>
              <div className="document-actions">
                <button
                  className="delete-button"
                  title="删除文档"
                  onClick={() => handleDelete(doc)}
                >
                  <img src={deleteIcon} alt="delete" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 删除确认对话框 */}
      {deleteConfirm.show && deleteConfirm.doc && (
        <div className="delete-confirm-modal">
          <div className="delete-confirm-dialog">
            {/* Header */}
            <div className="delete-confirm-header">
              <h3 className="delete-confirm-title">删除文档</h3>
              <button
                onClick={cancelDelete}
                className="delete-confirm-close"
                title="关闭"
              >
                <span>✕</span>
              </button>
            </div>

            {/* Content */}
            <div className="delete-confirm-content">
              <p>
                您即将永久删除文档 <span style={{ fontWeight: 500 }}>"{deleteConfirm.doc.name}"</span>，且无法恢复
              </p>
            </div>

            {/* Footer */}
            <div className="delete-confirm-footer">
              <button
                onClick={cancelDelete}
                className="delete-confirm-button cancel"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="delete-confirm-button delete"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentsTable
