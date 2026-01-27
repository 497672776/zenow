import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getBackendBaseUrl } from '../utils/backendPort'
import deleteIcon from '../assets/delete-icon.svg'
import editIcon from '../assets/edit-icon.svg'
import './HistoryPage.css'

interface HistoryItem {
  id: number
  session_name: string
  created_at: string
  updated_at: string
  message_count: number
  total_tokens: number
}

interface HistoryPageProps {
  onSelectSession?: (sessionId: number) => void
  refreshTrigger?: number
}

function HistoryPage({ onSelectSession, refreshTrigger }: HistoryPageProps) {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [renamingSessionId, setRenamingSessionId] = useState<number | null>(null)
  const [renameInput, setRenameInput] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; sessionId: number | null; sessionName: string }>({
    show: false,
    sessionId: null,
    sessionName: ''
  })
  const navigate = useNavigate()

  // 加载历史聊天记录
  useEffect(() => {
    loadHistory()
  }, [])

  // 监听refreshTrigger，当Sidebar删除/重命名时刷新列表
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      loadHistory()
    }
  }, [refreshTrigger])

  const loadHistory = async () => {
    try {
      setLoading(true)
      const apiUrl = await getBackendBaseUrl()
      const response = await fetch(`${apiUrl}/api/sessions?limit=100`)
      if (response.ok) {
        const data = await response.json()
        setHistoryItems(data.sessions || [])
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = (sessionId: number, sessionName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteConfirm({
      show: true,
      sessionId,
      sessionName
    })
  }

  const confirmDelete = async () => {
    if (!deleteConfirm.sessionId) return

    const sessionId = deleteConfirm.sessionId
    setDeleteConfirm({ show: false, sessionId: null, sessionName: '' })

    try {
      const apiUrl = await getBackendBaseUrl()
      const response = await fetch(`${apiUrl}/api/sessions/${sessionId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        // 从列表中移除已删除的项
        setHistoryItems(prev => prev.filter(item => item.id !== sessionId))
      } else {
        alert('删除失败')
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('删除失败')
    }
  }

  const cancelDelete = () => {
    setDeleteConfirm({ show: false, sessionId: null, sessionName: '' })
  }

  const handleItemClick = (sessionId: number) => {
    if (onSelectSession) {
      onSelectSession(sessionId)
    }
    // 跳转到聊天页面
    navigate('/')
  }

  const handleRename = (sessionId: number, currentName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setRenamingSessionId(sessionId)
    setRenameInput(currentName)
  }

  const handleRenameConfirm = async () => {
    if (!renamingSessionId || !renameInput.trim()) {
      return
    }

    try {
      const apiUrl = await getBackendBaseUrl()
      const response = await fetch(`${apiUrl}/api/sessions/${renamingSessionId}/name`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          new_name: renameInput.trim()
        })
      })

      if (response.ok) {
        // 更新本地列表中的名称
        const newName = renameInput.trim()
        setHistoryItems(prev =>
          prev.map(item =>
            item.id === renamingSessionId
              ? { ...item, session_name: newName }
              : item
          )
        )
        setRenamingSessionId(null)
        setRenameInput('')
      } else {
        alert('重命名失败')
      }
    } catch (error) {
      console.error('Failed to rename session:', error)
      alert('重命名失败')
    }
  }

  const handleRenameCancel = () => {
    setRenamingSessionId(null)
    setRenameInput('')
  }

  // 格式化时间戳为 YY/MM/DD HH:MM 格式
  const formatTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp)
      const year = date.getFullYear().toString().slice(2)
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${year}/${month}/${day} ${hours}:${minutes}`
    } catch (error) {
      console.error('Error formatting timestamp:', timestamp, error)
      return 'Unknown'
    }
  }

  return (
    <div className="history-page">
      {/* Main Content */}
      <div className="history-content">
        <div className="history-container">
          {/* Table Header */}
          <div className="history-table-header">
            <div className="header-label header-label-content">聊天内容</div>
            <div className="header-label header-label-time">创建时间</div>
            <div className="header-divider" />
          </div>

          {/* History List */}
          <div className="history-list">
            {loading ? (
              <div className="history-empty">加载中...</div>
            ) : historyItems.length === 0 ? (
              <div className="history-empty">暂无聊天记录</div>
            ) : (
              historyItems.map(item => (
                <div
                  key={item.id}
                  className="history-item"
                  onClick={() => handleItemClick(item.id)}
                >
                  <div className="history-item-question">
                    <span className="history-item-text">{item.session_name}</span>
                  </div>
                  <div className="history-item-time">
                    <span className="history-item-time-text">{formatTime(item.created_at)}</span>
                  </div>
                  <div className="history-item-actions">
                    <button
                      className="edit-button"
                      onClick={(e) => handleRename(item.id, item.session_name, e)}
                      aria-label="重命名"
                    >
                      <img src={editIcon} alt="" className="edit-icon" />
                    </button>
                    <button
                      className="delete-button"
                      onClick={(e) => handleDelete(item.id, item.session_name, e)}
                      aria-label="删除"
                    >
                      <img src={deleteIcon} alt="" className="delete-icon" />
                    </button>
                  </div>
                  <div className="history-item-divider" />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm.show && deleteConfirm.sessionId && (
        <div className="modal-overlay">
          <div className="modal-container">
            {/* Header */}
            <div className="modal-header">
              <h3 className="modal-title">删除聊天</h3>
              <button
                onClick={cancelDelete}
                className="modal-close-btn"
                title="关闭"
              >
                <span>✕</span>
              </button>
            </div>

            {/* Content */}
            <div className="modal-body">
              <p className="modal-text">
                您即将永久删除该聊天记录 <span className="modal-highlight">"{deleteConfirm.sessionName}"</span>，且无法恢复
              </p>
            </div>

            {/* Footer */}
            <div className="modal-footer">
              <button
                onClick={cancelDelete}
                className="modal-btn modal-btn-cancel"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="modal-btn modal-btn-delete"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {renamingSessionId && (
        <div className="modal-overlay">
          <div className="modal-container">
            <h3 className="modal-title">重命名聊天</h3>
            <input
              type="text"
              value={renameInput}
              onChange={(e) => setRenameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleRenameConfirm()
                }
              }}
              autoFocus
              className="modal-input"
              placeholder="输入新的聊天标题"
            />
            <div className="modal-footer">
              <button
                onClick={handleRenameCancel}
                className="modal-btn modal-btn-cancel"
              >
                取消
              </button>
              <button
                onClick={handleRenameConfirm}
                className="modal-btn modal-btn-confirm"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HistoryPage
