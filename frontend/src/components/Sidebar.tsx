import { useState, useEffect } from 'react'
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
}

function Sidebar({ currentSessionId, onSessionSelect, onNewChat }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (path: string) => {
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
