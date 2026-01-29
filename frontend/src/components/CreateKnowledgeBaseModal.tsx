import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import kbIcon5 from '../assets/kb-icon-5.png'
import { getBackendBaseUrl } from '../utils/backendPort'
import './CreateKnowledgeBaseModal.css'

interface CreateKnowledgeBaseModalProps {
  isOpen: boolean
  mode?: 'create' | 'edit'
  kbName?: string
  initialName?: string
  initialDescription?: string
  initialAvatarUrl?: string
  onClose: () => void
  onSuccess?: (kbName: string) => void
}

const CreateKnowledgeBaseModal: React.FC<CreateKnowledgeBaseModalProps> = ({
  isOpen,
  mode = 'create',
  kbName,
  initialName = '',
  initialDescription = '',
  initialAvatarUrl = '',
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [invalidCharToast, setInvalidCharToast] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const toastTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // 当 modal 打开或初始值变化时，重置表单
  useEffect(() => {
    if (isOpen) {
      setName(initialName)
      setDescription(initialDescription)
      setAvatarUrl(initialAvatarUrl)
      setAvatarFile(null)
      setError('')
      setInvalidCharToast('')
    }
  }, [isOpen, initialName, initialDescription, initialAvatarUrl])

  const handleAvatarClick = () => {
    fileInputRef.current?.click()
  }

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // 检查文件类型
      if (!file.type.startsWith('image/')) {
        setError('请选择图片文件')
        return
      }

      // 检查文件大小（限制为 5MB）
      if (file.size > 5 * 1024 * 1024) {
        setError('图片大小不能超过 5MB')
        return
      }

      // 保存File对象用于上传
      setAvatarFile(file)

      // 读取图片并转换为 base64 用于预览
      const reader = new FileReader()
      reader.onload = (event) => {
        const dataUrl = event.target?.result as string
        setAvatarUrl(dataUrl)
        setError('')
      }
      reader.readAsDataURL(file)
    }
  }

  const handleCreate = async () => {
    const newName = name.trim()

    if (!newName) {
      setError('知识库名称不能为空')
      return
    }

    if (newName.length > 25) {
      setError('知识库名称不能超过 25 个字符')
      return
    }

    setLoading(true)
    setError('')

    try {
      // 获取后端URL
      const baseUrl = await getBackendBaseUrl()

      if (mode === 'edit') {
        // 编辑模式 - 调用更新API
        // TODO: 替换为实际的API调用
        console.log('更新知识库:', {
          kbName,
          newName,
          description: description.trim(),
          avatarUrl
        })

        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))

        console.log('✅ 更新知识库成功')
        onSuccess?.(newName)
      } else {
        // 创建模式 - 调用创建API
        // 构建FormData
        const formData = new FormData()
        formData.append('name', newName)
        formData.append('description', description.trim())

        // 添加图片文件（如果有）
        if (avatarFile) {
          formData.append('avatar', avatarFile)
        }

        // 调试日志
        console.log('📤 发送创建知识库请求:', {
          name: newName,
          description: description.trim(),
          hasAvatar: !!avatarFile,
          url: `${baseUrl}/api/knowledge-bases`
        })

        // 打印 FormData 内容
        for (let pair of formData.entries()) {
          console.log('  -', pair[0], ':', pair[1])
        }

        // 发送请求
        const response = await fetch(`${baseUrl}/api/knowledge-bases`, {
          method: 'POST',
          body: formData
          // 注意：不要设置 Content-Type，浏览器会自动设置为 multipart/form-data
        })

        console.log('📥 响应状态:', response.status, response.statusText)

        if (!response.ok) {
          const errorText = await response.text()
          console.error('❌ 创建失败 (原始响应):', errorText)
          try {
            const errorData = JSON.parse(errorText)
            throw new Error(errorData.detail || '创建知识库失败')
          } catch (e) {
            throw new Error(errorText || '创建知识库失败')
          }
        }

        const result = await response.json()
        console.log('✅ 创建知识库成功:', result)

        // 重置表单
        resetForm()
        onSuccess?.(newName)
      }

      onClose()
    } catch (err) {
      console.error(mode === 'edit' ? '更新知识库失败:' : '创建知识库失败:', err)
      setError(err instanceof Error ? err.message : `${mode === 'edit' ? '更新' : '创建'}知识库失败，请重试`)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setName('')
    setDescription('')
    setAvatarUrl('')
    setAvatarFile(null)
    setError('')
    setInvalidCharToast('')
  }

  const handleClose = () => {
    if (!loading) {
      resetForm()
      onClose()
    }
  }

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // 只允许字母、数字、中文、下划线、连字符
    const validNamePattern = /^[\w\-\u4e00-\u9fff]*$/
    const newValue = e.target.value

    if (validNamePattern.test(newValue) || newValue === '') {
      setName(newValue)
      if (error) setError('')
      setInvalidCharToast('')
    } else {
      // 检测到非法字符，显示提示
      setInvalidCharToast('❌ 知识库名称只能包含字母、数字、中文、下划线和连字符')
      // 清除之前的定时器
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current)
      }
      // 3 秒后自动隐藏提示
      toastTimeoutRef.current = setTimeout(() => {
        setInvalidCharToast('')
      }, 3000)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading && name.trim()) {
      handleCreate()
    }
  }

  return createPortal(
    isOpen ? (
      <div className="modal-backdrop" onClick={handleClose}>
        {/* Modal Container */}
        <div className="modal-container" onClick={(e) => e.stopPropagation()}>
          <div className="modal-dialog">
            {/* Header */}
            <div className="modal-header">
              <h2 className="modal-title">{mode === 'edit' ? '编辑知识库' : '新建知识库'}</h2>
              <button
                onClick={handleClose}
                disabled={loading}
                className="modal-close-button"
              >
                <svg className="modal-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="modal-content">
              {/* Avatar */}
              <div className="avatar-section">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="avatar-input"
                  disabled={loading}
                />
                <div onClick={handleAvatarClick} className="avatar-upload">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="Avatar" />
                  ) : (
                    <img src={kbIcon5} alt="Default Avatar" />
                  )}
                </div>
              </div>

              {/* Name Input */}
              <div className="modal-form-section">
                <label className="form-label form-label-required">
                  知识库名称
                </label>
                <input
                  type="text"
                  placeholder="希望这么称呼您的知识库？"
                  value={name}
                  onChange={handleNameChange}
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                  maxLength={25}
                  className="form-input"
                />
                {invalidCharToast && (
                  <div className="invalid-char-toast">
                    {invalidCharToast}
                  </div>
                )}
                <div className={`form-char-count ${name.length > 25 ? 'warning' : 'normal'}`}>
                  {name.length}/25 字符
                </div>
              </div>

              {/* Description */}
              <div className="modal-form-section">
                <label className="form-label">
                  简介
                </label>
                <textarea
                  placeholder="请以简介介绍一遍，或者告诉大家是干什么用的吧。"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={loading}
                  rows={3}
                  maxLength={100}
                  className="form-textarea"
                />
                <div className={`form-char-count ${description.length > 100 ? 'warning' : 'normal'}`}>
                  {description.length}/100 字符
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="modal-footer">
              <button
                onClick={handleClose}
                disabled={loading}
                className="modal-button modal-button-cancel"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={loading || !name.trim()}
                className="modal-button modal-button-primary"
              >
                {loading ? (mode === 'edit' ? '更新中...' : '创建中...') : (mode === 'edit' ? '保存' : '创建')}
              </button>
            </div>
          </div>
        </div>
      </div>
    ) : null,
    document.body
  )
}

export default CreateKnowledgeBaseModal
