import { useEffect } from 'react'
import { checkBackendHealth } from '../utils/backendPort'
import launchPageBackground from '../assets/launch-page-background.png'
import launchPageLogo from '../assets/launch-page-logo.svg'
import './SplashPage.css'

interface SplashPageProps {
  onReady: () => void
}

function SplashPage({ onReady }: SplashPageProps) {

  useEffect(() => {
    let isMounted = true
    let retryCount = 0
    const maxRetries = 10

    const connectToBackend = async () => {
      while (retryCount < maxRetries && isMounted) {
        try {
          const isHealthy = await checkBackendHealth()

          if (isHealthy && isMounted) {
            onReady()
            return
          }
        } catch (error) {
          console.warn('Backend connection attempt failed:', error)
        }

        retryCount++
        if (retryCount < maxRetries && isMounted) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }
    }

    // 延迟500ms后开始检测，让启动页面先显示
    const timer = setTimeout(() => {
      connectToBackend()
    }, 500)

    return () => {
      isMounted = false
      clearTimeout(timer)
    }
  }, [onReady])

  return (
    <div className="splash-container">
      <div className="splash-content">
        {/* 背景层 - 充满整个画面，可拉伸 */}
        <img
          alt=""
          className="splash-background"
          src={launchPageBackground}
        />
        {/* Logo层 - 居中固定大小 */}
        <img
          alt="Zenow Logo"
          className="splash-logo"
          src={launchPageLogo}
        />
      </div>
    </div>
  )
}

export default SplashPage
