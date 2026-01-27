import { Link, useLocation, useNavigate } from 'react-router-dom'
import './Sidebar.css'
import SessionList from './SessionList'
import newChatSvg from '../assets/left-newchat.svg'
import kbSvg from '../assets/left-kb.svg'
import historySvg from '../assets/left-history.svg'
import settingSvg from '../assets/left-setting.svg'

interface SidebarProps {
  currentSessionId: number | null
  onSessionSelect: (sessionId: number) => void
  onNewChat: () => void
  refreshTrigger?: number  // 用于触发会话列表刷新
  isNewChatMode: boolean   // 是否为新对话模式
}

function Sidebar({ currentSessionId, onSessionSelect, onNewChat, refreshTrigger, isNewChatMode }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (path: string) => {
    // 如果是根路径，只有在新对话模式下才高亮
    if (path === '/') {
      return location.pathname === path && isNewChatMode ? 'active' : ''
    }
    return location.pathname === path ? 'active' : ''
  }

  // 处理会话选择
  const handleSessionSelect = (sessionId: number) => {
    onSessionSelect(sessionId)
    // 切换到聊天页面
    navigate('/')
  }

  // 处理新建会话
  const handleNewChat = () => {
    onNewChat()
    // 切换到聊天页面
    navigate('/')
  }

  return (
    <nav className="sidebar">
      {/* 导航按钮 */}
      <ul className="nav-links">
        <li>
          <Link to="/" className={`nav-link ${isActive('/')}`} onClick={handleNewChat}>
            <img src={newChatSvg} alt="New Chat" className="nav-icon" />
            <span>新对话</span>
          </Link>
        </li>
        <li>
          <Link to="/knowledge-base" className={`nav-link ${isActive('/knowledge-base')}`}>
            <img src={kbSvg} alt="Knowledge Base" className="nav-icon" />
            <span>知识库</span>
          </Link>
        </li>
        <li>
          <Link to="/history" className={`nav-link ${isActive('/history')}`}>
            <img src={historySvg} alt="History" className="nav-icon" />
            <span>历史聊天</span>
          </Link>
        </li>
      </ul>

      {/* 会话列表 */}
      <div className="sidebar-sessions">
        <SessionList
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
          refreshTrigger={refreshTrigger}
        />
      </div>

      {/* 底部设置 */}
      <div className="sidebar-footer">
        <Link to="/settings" className={`nav-link ${isActive('/settings')}`}>
          <img src={settingSvg} alt="Settings" className="nav-icon" />
          <span>设置</span>
        </Link>
      </div>
    </nav>
  )
}

export default Sidebar
