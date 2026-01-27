import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import HistoryPage from './pages/HistoryPage'
import SplashPage from './pages/SplashPage'
import TitleBar from './components/TitleBar'
import Sidebar from './components/Sidebar'
import './App.css'

function AppContent() {
  const location = useLocation()
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)  // 刷新触发器

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

  // 判断是否为新对话模式（没有选中会话）
  const isNewChatMode = currentSessionId === null

  // 触发会话列表刷新
  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1)
    console.log('App: 触发会话列表刷新')
  }

  return (
    <div className="app-container">
      <TitleBar pageTitle={getPageTitle()} />
      <div className="app">
        <Sidebar
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
          refreshTrigger={refreshTrigger}
          isNewChatMode={isNewChatMode}
        />
        <main className="main-content">
          <Routes>
            <Route
              path="/"
              element={
                <ChatPage
                  currentSessionId={currentSessionId}
                  onSessionChange={setCurrentSessionId}
                  onRefreshSessions={triggerRefresh}
                />
              }
            />
            <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
            <Route
              path="/history"
              element={
                <HistoryPage
                  onSelectSession={handleSessionSelect}
                  refreshTrigger={refreshTrigger}
                />
              }
            />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function App() {
  const [isReady, setIsReady] = useState(false)

  const handleSplashReady = () => {
    setIsReady(true)
  }

  // 显示启动页面，直到后端连接成功
  if (!isReady) {
    return <SplashPage onReady={handleSplashReady} />
  }

  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
