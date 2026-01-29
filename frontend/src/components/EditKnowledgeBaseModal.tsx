import React, { useState } from 'react'
import './EditKnowledgeBaseModal.css'

interface EditKnowledgeBaseModalProps {
  isOpen: boolean
  kbName: string
  initialName: string
  initialDescription: string
  initialAvatarUrl?: string
  onClose: () => void
  onSuccess: () => void
}

const EditKnowledgeBaseModal: React.FC<EditKnowledgeBaseModalProps> = ({
  isOpen,
  kbName,
  initialName,
  initialDescription,
  initialAvatarUrl,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState(initialName)
  const [description, setDescription] = useState(initialDescription)
  const [avatarUrl, setAvatarUrl] = useState(initialAvatarUrl || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      setError('知识库名称不能为空')
      return
    }

    setLoading(true)
    setError('')

    try {
      // TODO: 替换为实际的API调用
      console.log('更新知识库:', {
        kbName,
        newName: name,
        description,
        avatarUrl
      })

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      onSuccess()
    } catch (error) {
      console.error('Failed to update knowledge base:', error)
      setError('更新失败，请重试')
    } finally {
      setLoading(false)
    }
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[400px] overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">编辑知识库</h3>
          <button
            onClick={onClose}
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
              <div className="w-16 h-16 rounded-full overflow-hidden bg-gray-100 flex items-center justify-center">
                {avatarUrl ? (
                  <img src={avatarUrl} alt="头像" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-gray-400 text-2xl">📁</span>
                )}
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="text-sm text-gray-500 file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                disabled={loading}
              />
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
            />
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
            />
          </div>

          {/* 按钮 */}
          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              disabled={loading}
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EditKnowledgeBaseModal