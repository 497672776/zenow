import { useState, useEffect, useRef } from 'react'
import './SessionList.css'
import { getBackendBaseUrl } from '../utils/backendPort'

interface Session {
  id: number
  session_name: string
  created_at: string
  updated_at: string
  message_count: number
  total_tokens: number
  section?: 'today' | 'week' | 'older'
}

interface SessionListProps {
  currentSessionId: number | null
  onSessionSelect: (sessionId: number) => void
  onNewChat: () => void
  onDeleteSession?: (sessionId: number) => void
  onRenameSession?: (sessionId: number, newName: string) => void
  refreshTrigger?: number  // 用于触发刷新的计数器
}

let API_BASE_URL = 'http://localhost:8050'

function SessionList({ currentSessionId, onSessionSelect, onNewChat, onDeleteSession, onRenameSession, refreshTrigger }: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [menuOpenId, setMenuOpenId] = useState<number | null>(null)
  const [renamingSessionId, setRenamingSessionId] = useState<number | null>(null)
  const [renameInput, setRenameInput] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; sessionId: number | null; sessionName: string }>({
    show: false,
    sessionId: null,
    sessionName: ''
  })
  const menuRef = useRef<HTMLDivElement>(null)

  // 初始化后端 URL
  useEffect(() => {
    getBackendBaseUrl().then(url => {
      API_BASE_URL = url
      loadSessions()
    })
  }, [])

  // 监听 refreshTrigger 变化，重新加载会话列表
  useEffect(() => {
    if (refreshTrigger !== undefined && refreshTrigger > 0) {
      console.log('SessionList: 收到刷新触发器，重新加载会话列表')
      loadSessions()
    }
  }, [refreshTrigger])

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (menuRef.current && menuRef.current.contains(target)) {
        return
      }
      if (target.closest('.session-menu-btn')) {
        return
      }
      setMenuOpenId(null)
    }

    if (menuOpenId) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [menuOpenId])

  // 加载会话列表
  const loadSessions = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions?limit=100`)
      if (!response.ok) {
        throw new Error('加载会话列表失败')
      }
      const data = await response.json()

      console.log('SessionList: 加载到的会话数据:', data)

      // 按时间分组
      const now = new Date()
      const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

      const sessionsWithSection = data.sessions.map((session: Session) => {
        const updatedAt = new Date(session.updated_at)
        let section: 'today' | 'week' | 'older' = 'older'

        if (updatedAt >= todayStart) {
          section = 'today'
        } else if (updatedAt >= weekStart) {
          section = 'week'
        }

        return { ...session, section }
      })

      console.log('SessionList: 分组后的会话:', sessionsWithSection)
      setSessions(sessionsWithSection)
    } catch (error) {
      console.error('加载会话列表失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 处理会话选择
  const handleSessionSelect = (sessionId: number) => {
    onSessionSelect(sessionId)
  }

  // 处理重命名点击
  const handleRenameClick = (sessionId: number, currentName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setRenamingSessionId(sessionId)
    setRenameInput(currentName)
    setMenuOpenId(null)
  }

  // 确认重命名
  const handleRenameConfirm = async () => {
    if (!renamingSessionId || !renameInput.trim()) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions/${renamingSessionId}/name`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_name: renameInput.trim(),
        }),
      })

      if (!response.ok) {
        throw new Error('重命名失败')
      }

      // 更新本地列表
      const newName = renameInput.trim()
      setSessions(prev =>
        prev.map(session =>
          session.id === renamingSessionId
            ? { ...session, session_name: newName }
            : session
        )
      )

      // 通知父组件
      onRenameSession?.(renamingSessionId, newName)

      setRenamingSessionId(null)
      setRenameInput('')
    } catch (error) {
      console.error('重命名失败:', error)
      alert('重命名失败: ' + (error instanceof Error ? error.message : '未知错误'))
    }
  }

  // 取消重命名
  const handleRenameCancel = () => {
    setRenamingSessionId(null)
    setRenameInput('')
  }

  // 处理删除点击
  const handleDeleteClick = (sessionId: number, sessionName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteConfirm({
      show: true,
      sessionId,
      sessionName
    })
    setMenuOpenId(null)
  }

  // 确认删除
  const confirmDelete = async () => {
    if (!deleteConfirm.sessionId) return

    const sessionId = deleteConfirm.sessionId
    setDeleteConfirm({ show: false, sessionId: null, sessionName: '' })

    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('删除失败')
      }

      // 从列表中移除
      setSessions(prev => prev.filter(session => session.id !== sessionId))

      // 如果删除的是当前会话，创建新会话
      if (sessionId === currentSessionId) {
        onNewChat()
      }

      // 通知父组件
      onDeleteSession?.(sessionId)
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败: ' + (error instanceof Error ? error.message : '未知错误'))
    }
  }

  // 取消删除
  const cancelDelete = () => {
    setDeleteConfirm({ show: false, sessionId: null, sessionName: '' })
  }

  // 按分组过滤会话
  const todaySessions = sessions.filter(s => s.section === 'today')
  const weekSessions = sessions.filter(s => s.section === 'week')
  const olderSessions = sessions.filter(s => s.section === 'older')

  console.log('SessionList 渲染:', {
    total: sessions.length,
    today: todaySessions.length,
    week: weekSessions.length,
    older: olderSessions.length,
    isLoading
  })

  return (
    <div className="session-list">

      {/* 会话分组 */}
      <div className="session-list-content">
        {isLoading ? (
          <div className="session-empty">加载中...</div>
        ) : sessions.length === 0 ? (
          <div className="session-empty">
            <p>暂无会话历史</p>
            <p>开始新对话创建会话</p>
          </div>
        ) : (
          <>
            {/* 今天 */}
            {todaySessions.length > 0 && (
              <div className="session-section">
                <div className="section-header">
                  <span>今天</span>
                </div>
                {todaySessions.map(session => (
                  <div key={session.id} className="session-item-wrapper">
                    <button
                      className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                      onClick={() => handleSessionSelect(session.id)}
                    >
                      <span className="session-title">{session.session_name}</span>

                      {/* 三点菜单按钮 */}
                      <div
                        className="session-menu-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          setMenuOpenId(menuOpenId === session.id ? null : session.id)
                        }}
                        title="更多操作"
                      >
                        <div className="ellipsis-icon">
                          <div className="dot"></div>
                          <div className="dot"></div>
                          <div className="dot"></div>
                        </div>
                      </div>
                    </button>

                    {/* 下拉菜单 */}
                    {menuOpenId === session.id && (
                      <div className="session-dropdown" ref={menuRef}>
                        <button
                          className="dropdown-item"
                          onClick={(e) => handleRenameClick(session.id, session.session_name, e)}
                        >
                          重命名
                        </button>
                        <button
                          className="dropdown-item delete"
                          onClick={(e) => handleDeleteClick(session.id, session.session_name, e)}
                        >
                          删除
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 7天内 */}
            {weekSessions.length > 0 && (
              <div className="session-section">
                <div className="section-header">
                  <span>7 天内</span>
                </div>
                {weekSessions.map(session => (
                  <div key={session.id} className="session-item-wrapper">
                    <button
                      className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                      onClick={() => handleSessionSelect(session.id)}
                    >
                      <span className="session-title">{session.session_name}</span>

                      {/* 三点菜单按钮 */}
                      <div
                        className="session-menu-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          setMenuOpenId(menuOpenId === session.id ? null : session.id)
                        }}
                        title="更多操作"
                      >
                        <div className="ellipsis-icon">
                          <div className="dot"></div>
                          <div className="dot"></div>
                          <div className="dot"></div>
                        </div>
                      </div>
                    </button>

                    {/* 下拉菜单 */}
                    {menuOpenId === session.id && (
                      <div className="session-dropdown" ref={menuRef}>
                        <button
                          className="dropdown-item"
                          onClick={(e) => handleRenameClick(session.id, session.session_name, e)}
                        >
                          重命名
                        </button>
                        <button
                          className="dropdown-item delete"
                          onClick={(e) => handleDeleteClick(session.id, session.session_name, e)}
                        >
                          删除
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 更早 */}
            {olderSessions.length > 0 && (
              <div className="session-section">
                <div className="section-header">
                  <span>更早</span>
                </div>
                {olderSessions.map(session => (
                  <div key={session.id} className="session-item-wrapper">
                    <button
                      className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                      onClick={() => handleSessionSelect(session.id)}
                    >
                      <span className="session-title">{session.session_name}</span>

                      {/* 三点菜单按钮 */}
                      <div
                        className="session-menu-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          setMenuOpenId(menuOpenId === session.id ? null : session.id)
                        }}
                        title="更多操作"
                      >
                        <div className="ellipsis-icon">
                          <div className="dot"></div>
                          <div className="dot"></div>
                          <div className="dot"></div>
                        </div>
                      </div>
                    </button>

                    {/* 下拉菜单 */}
                    {menuOpenId === session.id && (
                      <div className="session-dropdown" ref={menuRef}>
                        <button
                          className="dropdown-item"
                          onClick={(e) => handleRenameClick(session.id, session.session_name, e)}
                        >
                          重命名
                        </button>
                        <button
                          className="dropdown-item delete"
                          onClick={(e) => handleDeleteClick(session.id, session.session_name, e)}
                        >
                          删除
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* 删除确认模态框 */}
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

      {/* 重命名模态框 */}
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

export default SessionList
