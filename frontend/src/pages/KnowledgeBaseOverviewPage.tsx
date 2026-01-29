import React, { useState, useEffect } from 'react'
import CreateKnowledgeBaseModal from '../components/CreateKnowledgeBaseModal'
import { getBackendBaseUrl } from '../utils/backendPort'

// 知识库图标
import kbIcon5 from '../assets/kb-icon-5.png'
import editIcon from '../assets/edit-icon.svg'
import deleteIcon from '../assets/delete-icon.svg'
import './KnowledgeBaseOverviewPage.css'

interface KnowledgeBase {
  id: string | number
  name: string
  description?: string
  doc_count: number
  total_size: number
  created_at: string
  updated_at: string
  avatar_url?: string
}

interface KnowledgeBaseOverviewPageProps {
  onSelectKB?: (kbId: string, kbName: string) => void
}

interface MenuPosition {
  top: number
  left: number
}

const KnowledgeBaseOverviewPage: React.FC<KnowledgeBaseOverviewPageProps> = ({ onSelectKB }) => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [menuPosition, setMenuPosition] = useState<MenuPosition | null>(null)
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; kbName: string | null; kbTitle: string }>(
    { show: false, kbName: null, kbTitle: '' }
  )
  const [backendBaseUrl, setBackendBaseUrl] = useState<string>('')

  // 获取完整的头像 URL
  const getAvatarUrl = (avatarUrl: string | null | undefined) => {
    if (!avatarUrl) {
      console.log('📷 头像 URL 为空，使用默认图标')
      return kbIcon5
    }
    if (avatarUrl.startsWith('http')) {
      console.log('📷 头像 URL (绝对路径):', avatarUrl)
      return avatarUrl
    }
    const fullUrl = `${backendBaseUrl}${avatarUrl}`
    console.log('📷 头像 URL (拼接后):', fullUrl)
    return fullUrl
  }

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  const loadKnowledgeBases = async () => {
    setLoading(true)
    try {
      console.log('📡 正在加载知识库列表...')

      const baseUrl = await getBackendBaseUrl()
      setBackendBaseUrl(baseUrl)
      const response = await fetch(`${baseUrl}/api/knowledge-bases`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.success && data.knowledge_bases) {
        console.log(`✅ 成功加载 ${data.knowledge_bases.length} 个知识库`)
        setKnowledgeBases(data.knowledge_bases)
      } else {
        console.warn('⚠️ 响应格式不正确:', data)
        setKnowledgeBases([])
      }
    } catch (error) {
      console.error('❌ 加载知识库列表失败:', error)
      setKnowledgeBases([])
    } finally {
      setLoading(false)
    }
  }

  const handleCreateKB = () => {
    setShowCreateModal(true)
  }

  const formatRelativeTime = (dateString: string): string => {
    try {
      const normalizedDateString = dateString && !dateString.endsWith('Z') && dateString.includes('T')
        ? `${dateString}Z`
        : dateString

      const date = new Date(normalizedDateString)

      if (isNaN(date.getTime())) {
        console.warn('Invalid date string:', dateString)
        return dateString
      }

      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffMinutes = Math.floor(diffMs / (1000 * 60))

      if (diffMinutes < 1) return '刚刚更新'
      if (diffMinutes < 60) return `${diffMinutes}分钟前更新`
      if (diffHours < 24) return `${diffHours}小时前更新`
      if (diffDays === 1) return '昨天更新'
      if (diffDays <= 6) return `${diffDays}天前更新`
      if (diffDays <= 30) return '上周更新'
      if (diffDays <= 365) return '上月更新'
      return '去年更新'
    } catch (error) {
      console.error('Error formatting relative time:', dateString, error)
      return dateString
    }
  }

  const handleRename = (kb: KnowledgeBase, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingKb(kb)
    setOpenMenuId(null)
  }

  const handleDelete = (kbName: string, kbTitle: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteConfirm({
      show: true,
      kbName,
      kbTitle
    })
    setOpenMenuId(null)
  }

  const confirmDelete = async () => {
    if (!deleteConfirm.kbName) return

    const kbName = deleteConfirm.kbName
    const kbTitle = deleteConfirm.kbTitle
    setDeleteConfirm({ show: false, kbName: null, kbTitle: '' })

    try {
      console.log(`🗑️ 正在删除知识库: "${kbTitle}"`)

      const baseUrl = await getBackendBaseUrl()
      const response = await fetch(`${baseUrl}/api/knowledge-bases/by-name/${encodeURIComponent(kbName)}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '删除失败')
      }

      const result = await response.json()
      console.log(`✅ 删除成功:`, result)

      console.log(`📡 删除完成，现在刷新知识库列表...`)
      await loadKnowledgeBases()
      console.log(`✅ 列表已刷新`)
    } catch (error) {
      console.error('❌ 删除知识库失败:', error)
      alert(`删除失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  const cancelDelete = () => {
    setDeleteConfirm({ show: false, kbName: null, kbTitle: '' })
  }

  return (
    <div className="dataset-list">
      {/* 主内容 - 可滚动区域 */}
      <div className="dataset-list-content">
        {/* 居中内容容器 (848px) */}
        <div className="dataset-list-container">
          <div className="dataset-list-wrapper">
            {loading ? (
              <div className="loading-container">
                <div className="loading-text">加载中...</div>
              </div>
            ) : (
              <>
                {/* 个人知识库部分 */}
                <section>
                  <div className="section-header">
                    <h2 className="section-title">个人知识库</h2>
                    <button onClick={handleCreateKB} className="create-kb-button">
                      <div className="create-kb-icon">
                        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                          <path d="M5 2V8M2 5H8" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                      </div>
                      <span className="create-kb-text">新建知识库</span>
                    </button>
                  </div>
                </section>

                {/* 知识库网格 */}
                {knowledgeBases.filter(kb => kb.name !== 'image_search_kb').length > 0 && (
                  <div className="dataset-grid">
                    {knowledgeBases.filter(kb => kb.name !== 'image_search_kb').map((kb) => (
                      <div
                        key={kb.id}
                        className="dataset-card"
                        onClick={() => onSelectKB?.(String(kb.id), kb.name)}
                      >
                        <div className="dataset-card-content">
                          <div className="dataset-card-header">
                            {/* 知识库头像 */}
                            <div className="dataset-avatar">
                              <img
                                src={getAvatarUrl(kb.avatar_url)}
                                alt={kb.name}
                                onLoad={() => console.log('✅ 头像加载成功:', getAvatarUrl(kb.avatar_url))}
                                onError={() => console.error('❌ 头像加载失败:', getAvatarUrl(kb.avatar_url))}
                              />
                            </div>

                            {/* 知识库信息 */}
                            <div className="dataset-info">
                              <div className="dataset-info-inner">
                                <p className="dataset-name">
                                  {kb.name.length > 12 ? kb.name.substring(0, 12) + '...' : kb.name}
                                </p>
                                <div className="dataset-meta">
                                  <p>{kb.doc_count}个文件</p>
                                  <p>{formatRelativeTime(kb.updated_at)}</p>
                                </div>
                              </div>
                            </div>

                            {/* 菜单按钮 */}
                            <div className="dataset-menu-wrapper" onClick={(e) => e.stopPropagation()}>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (openMenuId === String(kb.id)) {
                                    setOpenMenuId(null)
                                    setMenuPosition(null)
                                  } else {
                                    const button = e.currentTarget
                                    const rect = button.getBoundingClientRect()
                                    setMenuPosition({
                                      top: rect.bottom + 8,
                                      left: rect.left - 100,
                                    })
                                    setOpenMenuId(String(kb.id))
                                  }
                                }}
                                className="dataset-menu-button"
                              >
                                ⋯
                              </button>

                              {/* 菜单下拉 */}
                              {openMenuId === String(kb.id) && menuPosition && (
                                <div
                                  className="dataset-menu"
                                  style={{
                                    top: `${menuPosition.top}px`,
                                    left: `${menuPosition.left}px`,
                                  }}
                                >
                                  <button
                                    onClick={(e) => handleRename(kb, e)}
                                    className="dataset-menu-item"
                                  >
                                    <img src={editIcon} alt="edit" />
                                    <span>重命名</span>
                                  </button>
                                  <button
                                    onClick={(e) => handleDelete(kb.name, kb.name, e)}
                                    className="dataset-menu-item delete"
                                  >
                                    <img src={deleteIcon} alt="delete" />
                                    <span>删除</span>
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* 删除确认对话框 */}
      {deleteConfirm.show && deleteConfirm.kbName && (
        <div className="delete-confirm-modal">
          <div className="delete-confirm-dialog">
            {/* 头部 */}
            <div className="delete-confirm-header">
              <h3 className="delete-confirm-title">删除知识库</h3>
              <button onClick={cancelDelete} className="delete-confirm-close" title="关闭">
                <span>✕</span>
              </button>
            </div>

            {/* 内容 */}
            <div className="delete-confirm-content">
              <p className="delete-confirm-text">
                您即将永久删除该知识库 <span className="delete-confirm-kb-name">"{deleteConfirm.kbTitle}"</span>，且无法恢复
              </p>
            </div>

            {/* 底部 */}
            <div className="delete-confirm-footer">
              <button onClick={cancelDelete} className="delete-confirm-button cancel">
                取消
              </button>
              <button onClick={confirmDelete} className="delete-confirm-button delete">
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑知识库对话框 */}
      {editingKb && (
        <CreateKnowledgeBaseModal
          isOpen={true}
          mode="edit"
          kbName={editingKb.name}
          initialName={editingKb.name}
          initialDescription={editingKb.description || ''}
          initialAvatarUrl={editingKb.avatar_url}
          onClose={() => setEditingKb(null)}
          onSuccess={async () => {
            setEditingKb(null)
            await loadKnowledgeBases()
          }}
        />
      )}

      {/* 创建知识库对话框 */}
      <CreateKnowledgeBaseModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={async (kbName: string) => {
          setShowCreateModal(false)
          try {
            console.log(`📝 知识库 "${kbName}" 创建成功，准备刷新列表...`)
            await new Promise(resolve => setTimeout(resolve, 200))
            await loadKnowledgeBases()
            console.log(`✅ 知识库 "${kbName}" 创建完成，列表已刷新`)
          } catch (error) {
            console.error('❌ 刷新列表失败:', error)
            setTimeout(() => {
              console.log('🔄 重新尝试刷新列表...')
              loadKnowledgeBases()
            }, 500)
          }
        }}
      />
    </div>
  )
}

export default KnowledgeBaseOverviewPage
