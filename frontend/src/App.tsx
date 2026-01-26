import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import HistoryPage from './pages/HistoryPage'
import TitleBar from './components/TitleBar'
import Sidebar from './components/Sidebar'
import './App.css'

function AppContent() {
  const location = useLocation()
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)

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

  // 处理会话选择
  const handleSessionSelect = (sessionId: number) => {
    setCurrentSessionId(sessionId)
  }

  // 处理新建会话
  const handleNewChat = () => {
    setCurrentSessionId(null)
  }

  return (
    <div className="app-container">
      <TitleBar pageTitle={getPageTitle()} />
      <div className="app">
        <Sidebar
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
        />
        <main className="main-content">
          <Routes>
            <Route
              path="/"
              element={
                <ChatPage
                  currentSessionId={currentSessionId}
                  onSessionChange={setCurrentSessionId}
                />
              }
            />
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
