import { useState, useEffect } from 'react'
import './SessionList.css'
import { getBackendBaseUrl } from '../utils/backendPort'

interface Session {
  id: number
  session_name: string
  created_at: string
  updated_at: string
  message_count: number
  total_tokens: number
}

interface SessionListProps {
  currentSessionId: number | null
  onSessionSelect: (sessionId: number) => void
  onNewChat: () => void
}

let API_BASE_URL = 'http://localhost:8050'

function SessionList({ currentSessionId, onSessionSelect, onNewChat }: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // 初始化后端 URL
  useEffect(() => {
    getBackendBaseUrl().then(url => {
      API_BASE_URL = url
      loadSessions()
    })
  }, [])

  // 加载会话列表
  const loadSessions = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions?limit=50`)
      if (!response.ok) {
        throw new Error('加载会话列表失败')
      }
      const data = await response.json()
      setSessions(data.sessions)
    } catch (error) {
      console.error('加载会话列表失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 删除会话
  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation() // 阻止触发选择事件

    if (!confirm('确定要删除这个会话吗？')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('删除会话失败')
      }

      // 如果删除的是当前会话，创建新会话
      if (sessionId === currentSessionId) {
        onNewChat()
      }

      // 重新加载会话列表
      loadSessions()
    } catch (error) {
      console.error('删除会话失败:', error)
      alert('删除会话失败: ' + (error instanceof Error ? error.message : '未知错误'))
    }
  }

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
      return '昨天'
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  }

  return (
    <div className="session-list">
      <div className="session-list-header">
        <h3>会话历史</h3>
        <button className="refresh-button" onClick={loadSessions} disabled={isLoading}>
          {isLoading ? '加载中...' : '刷新'}
        </button>
      </div>

      <div className="session-list-content">
        {sessions.length === 0 ? (
          <div className="empty-sessions">
            <p>暂无会话历史</p>
            <p>开始新对话创建会话</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
              onClick={() => onSessionSelect(session.id)}
            >
              <div className="session-item-header">
                <span className="session-name">{session.session_name}</span>
                <button
                  className="delete-button"
                  onClick={(e) => handleDeleteSession(session.id, e)}
                  title="删除会话"
                >
                  ×
                </button>
              </div>
              <div className="session-item-footer">
                <span className="session-time">{formatTime(session.updated_at)}</span>
                <span className="session-stats">
                  {session.message_count} 条消息
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default SessionList
