import React, { useState, useRef } from 'react'
import './CreateKnowledgeBaseModal.css'

interface CreateKnowledgeBaseModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: (kbName: string) => void
}

const CreateKnowledgeBaseModal: React.FC<CreateKnowledgeBaseModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      setError('知识库名称不能为空')
      return
    }

    // 检查名称是否包含特殊字符
    const invalidChars = /[<>:"/\\|?*]/
    if (invalidChars.test(name)) {
      setError('知识库名称不能包含特殊字符 < > : " / \\ | ? *')
      return
    }

    setLoading(true)
    setError('')

    try {
      // TODO: 替换为实际的API调用
      console.log('创建知识库:', {
        name: name.trim(),
        description: description.trim(),
        avatarUrl
      })

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      onSuccess?.(name.trim())

      // 重置表单
      setName('')
      setDescription('')
      setAvatarUrl('')
    } catch (error) {
      console.error('Failed to create knowledge base:', error)
      setError('创建失败，请重试')
    } finally {
      setLoading(false)
    }
  }

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

      // 读取图片并转换为 base64
      const reader = new FileReader()
      reader.onload = (event) => {
        const dataUrl = event.target?.result as string
        setAvatarUrl(dataUrl)
        setError('')
      }
      reader.readAsDataURL(file)
    }
  }

  const handleClose = () => {
    if (!loading) {
      setName('')
      setDescription('')
      setAvatarUrl('')
      setError('')
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[400px] overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">新建知识库</h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            ✕
          </button>
        </div>

        {/* 内容 */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* 头像 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              头像
            </label>
            <div className="flex items-center space-x-4">
              <div
                className="w-16 h-16 rounded-full overflow-hidden bg-gray-100 flex items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={handleAvatarClick}
              >
                {avatarUrl ? (
                  <img src={avatarUrl} alt="头像" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-gray-400 text-2xl">📁</span>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
                disabled={loading}
              />
              <button
                type="button"
                onClick={handleAvatarClick}
                className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
                disabled={loading}
              >
                选择图片
              </button>
            </div>
          </div>

          {/* 名称 */}
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              知识库名称 *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="请输入知识库名称"
              disabled={loading}
              required
              maxLength={50}
            />
            <p className="text-xs text-gray-500 mt-1">
              不能包含特殊字符 &lt; &gt; : " / \ | ? *
            </p>
          </div>

          {/* 描述 */}
          <div className="mb-6">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              描述
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              placeholder="请输入知识库描述（可选）"
              disabled={loading}
              maxLength={200}
            />
          </div>

          {/* 按钮 */}
          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              disabled={loading}
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading || !name.trim()}
            >
              {loading ? '创建中...' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateKnowledgeBaseModal