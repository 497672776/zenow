import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import HistoryPage from './pages/HistoryPage'
import TitleBar from './components/TitleBar'
import './App.css'
import newChatSvg from './assets/left-newchat.svg'
import kbSvg from './assets/left-kb.svg'
import historySvg from './assets/left-history.svg'
import settingSvg from './assets/left-setting.svg'

function Sidebar() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path ? 'active' : ''
  }

  return (
    <nav className="sidebar">


      <ul className="nav-links">
        <li>
          <Link to="/" className={`nav-link ${isActive('/')}`}>
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

      <div className="sidebar-footer">
        <Link to="/settings" className={`nav-link ${isActive('/settings')}`}>
          <img src={settingSvg} alt="Settings" className="nav-icon" />
          <span>设置</span>
        </Link>
      </div>
    </nav>
  )
}

function AppContent() {
  const location = useLocation()

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return '新对话'
      case '/knowledge-base':
        return '知识库'
      case '/history':
        return '历史聊天'
      case '/settings':
        return '设置'
      default:
        return '新对话'
    }
  }

  return (
    <div className="app-container">
      <TitleBar pageTitle={getPageTitle()} />
      <div className="app">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
