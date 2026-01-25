import { useState, useEffect } from 'react'
import './TitleBar.css'
import logoSvg from '../assets/spacemit_ai.svg'

interface TitleBarProps {
  pageTitle: string
}

function TitleBar({ pageTitle }: TitleBarProps) {
  const [isMaximized, setIsMaximized] = useState(false)

  useEffect(() => {
    // 监听窗口最大化/还原状态
    // @ts-ignore
    const handleMaximizeChange = (_event: any, maximized: boolean) => {
      setIsMaximized(maximized)
    }

    // @ts-ignore
    window.electronAPI?.on('window-maximized', handleMaximizeChange)

    // 清理监听器
    return () => {
      // @ts-ignore
      window.electronAPI?.removeListener('window-maximized', handleMaximizeChange)
    }
  }, [])

  const handleMinimize = () => {
    // @ts-ignore
    window.electronAPI?.send('window-minimize')
  }

  const handleMaximize = () => {
    // @ts-ignore
    window.electronAPI?.send('window-maximize')
  }

  const handleClose = () => {
    // @ts-ignore
    window.electronAPI?.send('window-close')
  }

  return (
    <div className="title-bar">
      <div className="title-bar-section title-bar-left-section">
        <img src={logoSvg} alt="Spacemit AI" className="title-bar-logo" />
      </div>
      <div className="title-bar-section title-bar-right-section">
        <div className="title-bar-page-title">{pageTitle}</div>
        <div className="title-bar-drag-region"></div>
        <div className="title-bar-controls">
          <button className="title-bar-button minimize" onClick={handleMinimize} title="最小化">
            <svg width="12" height="12" viewBox="0 0 12 12">
              <path d="M1,6 L11,6" stroke="currentColor" strokeWidth="1" />
            </svg>
          </button>
          <button
            className="title-bar-button maximize"
            onClick={handleMaximize}
            title={isMaximized ? "还原" : "最大化"}
          >
            {isMaximized ? (
              // 还原图标（两个重叠的方框）
              <svg width="12" height="12" viewBox="0 0 12 12">
                <rect x="2" y="0" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1" />
                <rect x="0" y="2" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1" />
              </svg>
            ) : (
              // 最大化图标（单个方框）
              <svg width="12" height="12" viewBox="0 0 12 12">
                <rect x="1" y="1" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1" />
              </svg>
            )}
          </button>
          <button className="title-bar-button close" onClick={handleClose} title="关闭">
            <svg width="12" height="12" viewBox="0 0 12 12">
              <path d="M2,2 L10,10 M10,2 L2,10" stroke="currentColor" strokeWidth="1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

export default TitleBar
