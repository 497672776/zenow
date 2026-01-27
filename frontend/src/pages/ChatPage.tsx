import { useState, useEffect, useRef } from 'react'
import './ChatPage.css'
import { getBackendBaseUrl } from '../utils/backendPort'

// 消息接口定义：每条消息包含角色（用户/助手）和内容
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// ChatPage Props
interface ChatPageProps {
  currentSessionId: number | null
  onSessionChange: (sessionId: number | null) => void
  onRefreshSessions: () => void  // 刷新会话列表的回调
}

// 后端API的基础URL
let API_BASE_URL = 'http://localhost:8050' // Default fallback

function ChatPage({ currentSessionId, onSessionChange, onRefreshSessions }: ChatPageProps) {
  // ===== 状态管理 =====
  const [messages, setMessages] = useState<Message[]>([])  // 存储所有聊天消息
  const [input, setInput] = useState('')  // 用户当前输入的文本
  const [isLoading, setIsLoading] = useState(false)  // 是否正在等待AI回复
  const [lastLoadedSessionId, setLastLoadedSessionId] = useState<number | null>(null)  // 记录上次加载的会话ID
  const messagesEndRef = useRef<HTMLDivElement>(null)  // 用于滚动到消息底部的引用

  // 判断是否是新对话模式（没有 session_id）
  const isNewChatMode = currentSessionId === null

  // ===== 生命周期：组件加载时执行 =====
  useEffect(() => {
    // 初始化后端 URL
    getBackendBaseUrl().then(url => {
      API_BASE_URL = url
      console.log('Using backend URL:', API_BASE_URL)
    })
  }, [])

  // ===== 监听会话ID变化，加载会话历史 =====
  useEffect(() => {
    if (currentSessionId !== null && currentSessionId !== lastLoadedSessionId) {
      // 会话ID变化且不是刚创建的会话，加载历史消息
      loadSessionMessages(currentSessionId)
      setLastLoadedSessionId(currentSessionId)
    } else if (currentSessionId === null) {
      // 新会话，清空消息
      setMessages([])
      setLastLoadedSessionId(null)
    }
  }, [currentSessionId])

  // ===== 加载会话消息 =====
  const loadSessionMessages = async (sessionId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/messages`)
      if (!response.ok) {
        throw new Error('加载会话消息失败')
      }

      const data = await response.json()
      const loadedMessages: Message[] = data.messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
      }))

      setMessages(loadedMessages)
      console.log('加载会话:', sessionId, '消息数:', loadedMessages.length)
    } catch (error) {
      console.error('加载会话失败:', error)
    }
  }

  // ===== 生命周期：当消息列表变化时执行 =====
  useEffect(() => {
    // 每当消息列表更新，自动滚动到最底部，显示最新消息
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ===== 发送消息的核心函数 =====
  const handleSend = async () => {
    // 1. 验证输入：如果输入为空，直接返回
    if (!input.trim()) return

    // 2. 创建用户消息对象
    const userMessage: Message = {
      role: 'user',
      content: input,
    }

    // 保存用户输入
    const userInput = input
    setInput('')

    // 3. 新对话模式：创建会话并跳转
    if (isNewChatMode) {
      try {
        setIsLoading(true)

        // 创建新会话
        const createSessionResponse = await fetch(`${API_BASE_URL}/api/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            first_message: userInput,
          }),
        })

        if (!createSessionResponse.ok) {
          throw new Error('创建会话失败')
        }

        const sessionData = await createSessionResponse.json()
        const newSessionId = sessionData.session_id

        console.log('创建新会话:', newSessionId, '会话名:', sessionData.session_name)

        // 更新父组件的 session_id
        onSessionChange(newSessionId)

        // 标记为已加载（避免 useEffect 重复加载）
        setLastLoadedSessionId(newSessionId)

        // 刷新会话列表（新会话已创建）
        onRefreshSessions()

        // 显示用户消息
        setMessages([userMessage])

        // 发送消息到新会话
        await sendMessageToSession(newSessionId, userMessage)

      } catch (error) {
        console.error('创建会话失败:', error)
        alert('创建会话失败: ' + (error instanceof Error ? error.message : '未知错误'))
        setIsLoading(false)
      }
      return
    }

    // 4. 历史对话模式：直接发送消息
    const currentMessages = [...messages, userMessage]
    setMessages(currentMessages)
    setIsLoading(true)

    await sendMessageToSession(currentSessionId!, userMessage)
  }

  // ===== 发送消息到指定会话 =====
  const sendMessageToSession = async (sessionId: number, userMessage: Message) => {
    try {
      // 发送POST请求到后端API（带会话ID）
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [userMessage],  // 只发送当前消息，历史由后端从数据库加载
          stream: true,  // 启用流式传输
          session_id: sessionId,  // 传递会话ID
        }),
      })

      // 6. 检查HTTP响应状态
      if (!response.ok) {
        throw new Error(`HTTP错误! 状态: ${response.status}`)
      }

      // 7. 获取响应流的读取器
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()  // 用于将二进制数据解码为文本

      if (!reader) {
        throw new Error('无法获取响应流读取器')
      }

      // 8. 创建助手消息，初始显示"正在思考..."
      let assistantMessage: Message = {
        role: 'assistant',
        content: '正在思考...',  // 初始占位文本
      }

      // 9. 立即添加到列表显示占位符
      let messageIndex = 0  // 记录助手消息在数组中的索引位置
      setMessages((prev) => {
        messageIndex = prev.length  // 获取添加前的长度作为索引
        return [...prev, assistantMessage]
      })
      let firstTokenReceived = false  // 标记是否已收到第一个token

      // 9.1 节流渲染辅助函数：立即渲染第一次更新，之后最多每20ms渲染一次
      let pendingUpdate = false  // 标记是否有待处理的更新
      let lastUpdateTime = 0  // 记录上次更新的时间戳

      const throttledUpdate = () => {
        const now = Date.now()

        // 如果是第一个token，清空"正在思考..."并显示实际内容
        if (!firstTokenReceived) {
          firstTokenReceived = true
          setIsLoading(false)  // 确保关闭loading状态
          lastUpdateTime = now
          // 第一个token时立即更新
          setMessages((prev) => {
            const newMessages = [...prev]
            newMessages[messageIndex] = {
              role: 'assistant',
              content: assistantMessage.content  // 此时content已经是实际内容（不再是"正在思考..."）
            }
            return newMessages
          })
          return
        }

        // 如果距离上次更新不足20ms，延迟更新
        if (now - lastUpdateTime < 20) {
          if (!pendingUpdate) {
            pendingUpdate = true

            // 计算还需要等待多久
            const delay = 20 - (now - lastUpdateTime)

            setTimeout(() => {
              pendingUpdate = false
              lastUpdateTime = Date.now()

              setMessages((prev) => {
                const newMessages = [...prev]
                newMessages[messageIndex] = {
                  role: 'assistant',
                  content: assistantMessage.content
                }
                return newMessages
              })
            }, delay)
          }
          return
        }

        // 立即更新UI
        lastUpdateTime = now
        setMessages((prev) => {
          const newMessages = [...prev]
          newMessages[messageIndex] = {
            role: 'assistant',
            content: assistantMessage.content
          }
          return newMessages
        })
      }

      // 10. 循环读取流式数据
      while (true) {
        // 10.1 读取一个数据块
        const { done, value } = await reader.read()
        if (done) {
          // 流结束：执行最后一次更新确保所有内容都显示
          if (firstTokenReceived) {
            setMessages((prev) => {
              const newMessages = [...prev]
              newMessages[messageIndex] = {
                role: 'assistant',
                content: assistantMessage.content
              }
              return newMessages
            })
          }
          setIsLoading(false)
          break
        }

        // 10.2 将二进制数据解码为文本
        const chunk = decoder.decode(value)

        // 10.3 按行分割（SSE格式是按行传输的）
        const lines = chunk.split('\n')

        // 10.4 处理每一行
        for (const line of lines) {
          // SSE格式：每行以"data: "开头
          if (line.startsWith('data: ')) {
            const data = line.slice(6)  // 去掉"data: "前缀

            // 特殊标记：[DONE]表示流结束
            if (data === '[DONE]') {
              // 执行最后一次更新
              if (firstTokenReceived) {
                setMessages((prev) => {
                  const newMessages = [...prev]
                  newMessages[messageIndex] = {
                    role: 'assistant',
                    content: assistantMessage.content
                  }
                  return newMessages
                })
              }
              setIsLoading(false)

              // 刷新会话列表（消息数和时间已更新）
              onRefreshSessions()

              return
            }

            try {
              // 10.5 解析JSON数据
              const parsed = JSON.parse(data)

              // 检查是否有错误
              if (parsed.error) {
                throw new Error(parsed.error)
              }

              // 10.6 提取AI生成的内容片段
              // OpenAI格式：choices[0].delta.content
              if (parsed.choices && parsed.choices[0]?.delta?.content) {
                const content = parsed.choices[0].delta.content

                // 10.7 累加内容到助手消息
                // 如果是第一个token，先清空"正在思考..."
                if (!firstTokenReceived) {
                  assistantMessage.content = content  // 替换掉"正在思考..."
                } else {
                  assistantMessage.content += content  // 后续token累加
                }

                // 10.8 使用节流函数更新UI（最多每20ms更新一次）
                throttledUpdate()
              }
            } catch (e) {
              // 忽略空数据的解析错误
              if (data !== '') {
                console.error('解析SSE数据失败:', e)
              }
            }
          }
        }
      }
    } catch (error) {
      // 11. 错误处理：显示错误消息
      console.error('发送消息失败:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，处理您的请求时出错了: ' + (error instanceof Error ? error.message : '未知错误'),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      // 12. 无论成功或失败，都要取消加载状态
      setIsLoading(false)
    }
  }

  // ===== 键盘事件处理 =====
  const handleKeyPress = (e: React.KeyboardEvent) => {
    // 按Enter键（不按Shift）时发送消息
    // Shift+Enter可以换行
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ===== 渲染UI =====
  return (
    <div className="chat-page">
      {/* 消息显示区域 */}
      <div className="messages-container">
        {/* 如果没有消息，显示欢迎界面 */}
        {messages.length === 0 ? (
          <div className="empty-state">
            {isNewChatMode ? (
              <>
                <h2>开始新对话</h2>
                <p>输入你的第一条消息来创建新会话</p>
              </>
            ) : (
              <>
                <h2>会话已加载</h2>
                <p>继续你的对话</p>
              </>
            )}
          </div>
        ) : (
          // 有消息时，循环渲染每条消息
          messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-role">
                {message.role === 'user' ? '你' : 'AI助手'}
              </div>
              <div className="message-content">{message.content}</div>
            </div>
          ))
        )}

        {/* 用于滚动定位的空div */}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="input-container">
        {/* 多行文本输入框 */}
        <textarea
          className="message-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="在这里输入你的消息..."
          rows={3}
        />
        {/* 发送按钮：加载中或输入为空时禁用 */}
        <button
          className="send-button"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          发送
        </button>
      </div>
    </div>
  )
}

export default ChatPage
