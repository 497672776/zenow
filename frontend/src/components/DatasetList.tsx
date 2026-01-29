import React, { useState, useEffect } from 'react'
import CreateKnowledgeBaseModal from './CreateKnowledgeBaseModal'
import EditKnowledgeBaseModal from './EditKnowledgeBaseModal'

// 知识库图标
import kbIcon5 from '../assets/kb-icon-5.svg'
import editIcon from '../assets/edit-icon.svg'
import deleteIcon from '../assets/delete-icon.svg'
import './DatasetList.css'

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

interface DatasetListProps {
  onSelectKB?: (kbId: string, kbName: string) => void
}

interface MenuPosition {
  top: number
  left: number
}

const DatasetList: React.FC<DatasetListProps> = ({ onSelectKB }) => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [menuPosition, setMenuPosition] = useState<MenuPosition | null>(null)
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; kbName: string | null; kbTitle: string }>(
    { show: false, kbName: null, kbTitle: '' }
  )

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  const loadKnowledgeBases = async () => {
    setLoading(true)
    try {
      // TODO: 替换为实际的API调用
      console.log('📡 正在加载知识库列表...')
      // 模拟API响应
      const mockData = {
        knowledge_bases: [
          {
            id: '1',
            name: '示例知识库',
            description: '这是一个示例知识库',
            doc_count: 5,
            total_size: 1024000,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            avatar_url: undefined
          }
        ]
      }

      if (mockData?.knowledge_bases) {
        console.log(`✅ 成功加载 ${mockData.knowledge_bases.length} 个知识库`)
        setKnowledgeBases(mockData.knowledge_bases)
      } else {
        console.warn('⚠️ 响应中没有 knowledge_bases 字段:', mockData)
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
    setDeleteConfirm({ show: false, kbName: null, kbTitle: '' })

    try {
      console.log(`🗑️ 正在删除知识库: "${kbName}"`)
      // TODO: 替换为实际的API调用
      console.log(`✅ 删除请求成功`)

      console.log(`📡 删除完成，现在刷新知识库列表...`)
      await loadKnowledgeBases()
      console.log(`✅ 列表已刷新`)
    } catch (error) {
      console.error('❌ 删除知识库失败:', error)
      alert('删除失败')
    }
  }

  const cancelDelete = () => {
    setDeleteConfirm({ show: false, kbName: null, kbTitle: '' })
  }

  return (
    <div className="flex-1 flex flex-col bg-white" style={{ position: 'relative', overflow: 'hidden' }}>
      {/* 主内容 - 可滚动区域 */}
      <div
        className="flex-1 overflow-y-auto overflow-x-hidden"
        style={{
          paddingTop: '60px',
          minHeight: 0,
          maxHeight: 'calc(100vh - 60px)',
        }}
      >
        {/* 居中内容容器 (848px) */}
        <div className="flex justify-center" style={{ paddingTop: '0px', paddingBottom: '16px' }}>
          <div style={{ width: '848px' }}>
            {loading ? (
              <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 160px)' }}>
                <div className="text-center">
                  <div className="text-lg text-gray-600">加载中...</div>
                </div>
              </div>
            ) : (
              <>
                {/* 个人知识库部分 */}
                <section>
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-[20px] font-['MiSans_VF:Demibold'] text-neutral-950 leading-[30px]">
                      个人知识库
                    </h2>
                    <button
                      onClick={handleCreateKB}
                      className="flex items-center gap-[6px] h-[30px] px-[12px] py-[6px] rounded-[32px] hover:bg-[rgba(0,0,0,0.04)] transition-colors"
                    >
                      <div className="bg-[#b0e237] rounded-[8px] size-[16px] flex items-center justify-center">
                        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                          <path d="M5 2V8M2 5H8" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                      </div>
                      <span className="font-['MiSans_VF:Medium'] text-[14px] text-black leading-[20px]">
                        新建知识库
                      </span>
                    </button>
                  </div>
                </section>

                {/* 知识库网格 */}
                {knowledgeBases.filter(kb => kb.name !== 'image_search_kb').length > 0 && (
                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', paddingTop: '12px', paddingBottom: '40px' }}>
                    {knowledgeBases.filter(kb => kb.name !== 'image_search_kb').map((kb) => (
                    <div
                      key={kb.id}
                      className="border border-[#f9f9fa] border-solid rounded-[12px] cursor-pointer hover:shadow-md transition-shadow group"
                      style={{ width: '272px' }}
                      onClick={() => onSelectKB?.(String(kb.id), kb.name)}
                    >
                      <div className="flex flex-col items-start px-[17px] pt-[18px] pb-[22px] w-[272px]">
                        <div className="flex gap-3 items-center w-full">
                          {/* 知识库头像 */}
                          <div className="relative shrink-0 size-[48px] rounded-full overflow-hidden flex items-center justify-center group-hover:shadow-lg transition-shadow">
                            <img
                              src={kb.avatar_url || kbIcon5}
                              alt={kb.name}
                              className="w-full h-full object-cover"
                            />
                          </div>

                          {/* 知识库信息 */}
                          <div style={{ flex: '1 0 0', minWidth: '1px', minHeight: '1px' }}>
                            <div className="flex flex-col gap-[6px]">
                              <p className="font-['MiSans_VF:Medium'] text-[16px] text-[#0d0d0d] leading-normal h-[21px] overflow-hidden text-ellipsis whitespace-nowrap">
                                {kb.name.length > 12 ? kb.name.substring(0, 12) + '...' : kb.name}
                              </p>
                              <div className="flex gap-3 items-center font-['MiSans_VF:Normal'] text-[12px] text-[rgba(0,0,0,0.5)] leading-normal">
                                <p className="overflow-ellipsis overflow-hidden whitespace-nowrap">
                                  {kb.doc_count}个文件
                                </p>
                                <p className="overflow-ellipsis overflow-hidden whitespace-nowrap">
                                  {formatRelativeTime(kb.updated_at)}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* 菜单按钮 */}
                          <div
                            className="flex-shrink-0"
                            onClick={(e) => e.stopPropagation()}
                          >
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
                              className="p-1 hover:bg-[rgba(0,0,0,0.04)] rounded-md transition-colors text-[16px]"
                            >
                              ⋯
                            </button>

                            {/* 菜单下拉 */}
                            {openMenuId === String(kb.id) && menuPosition && (
                              <div
                                className="fixed bg-white border border-[rgba(0,0,0,0.1)] rounded-[10px] shadow-lg z-50 min-w-[160px]"
                                style={{
                                  top: `${menuPosition.top}px`,
                                  left: `${menuPosition.left}px`,
                                }}
                              >
                                <button
                                  onClick={(e) => handleRename(kb, e)}
                                  className="w-full flex items-center gap-3 px-4 py-2 text-left text-black font-['MiSans_VF:Regular'] text-[14px] hover:bg-[rgba(0,0,0,0.04)] rounded-t-[8px] first:rounded-t-[8px]"
                                >
                                  <img src={editIcon} alt="edit" className="w-4 h-4" />
                                  <span>重命名</span>
                                </button>
                                <button
                                  onClick={(e) => handleDelete(kb.name, kb.name, e)}
                                  className="w-full flex items-center gap-3 px-4 py-2 text-left text-[#ff4d4f] font-['MiSans_VF:Regular'] text-[14px] hover:bg-[rgba(0,0,0,0.04)] rounded-b-[8px] last:rounded-b-[8px]"
                                >
                                  <img src={deleteIcon} alt="delete" className="w-4 h-4" />
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-[12px] shadow-[0px_6px_16px_0px_rgba(0,0,0,0.08),0px_3px_6px_-4px_rgba(0,0,0,0.12),0px_9px_28px_8px_rgba(0,0,0,0.05)] w-[360px] overflow-hidden relative">
            {/* 头部 */}
            <div className="flex items-center justify-between px-[24px] pt-[20px] pb-[8px]">
              <h3 style={{ fontWeight: 600 }} className="text-[16px] text-[rgba(0,0,0,0.88)]">
                删除知识库
              </h3>
              <button
                onClick={cancelDelete}
                className="p-1 hover:bg-[rgba(0,0,0,0.04)] rounded-[4px] transition-colors"
                title="关闭"
              >
                <span className="text-lg">✕</span>
              </button>
            </div>

            {/* 内容 */}
            <div className="px-[24px] pt-0 pb-[16px]">
              <p className="text-[14px] font-['MiSans_VF:Normal'] text-[rgba(0,0,0,0.88)]">
                您即将永久删除该知识库 <span className="font-['MiSans_VF:Medium']">"{deleteConfirm.kbTitle}"</span>，且无法恢复
              </p>
            </div>

            {/* 底部 */}
            <div className="flex gap-[8px] items-center justify-end px-[24px] py-[20px]">
              <button
                onClick={cancelDelete}
                className="h-[32px] px-[24px] border border-[rgba(0,0,0,0.1)] bg-white rounded-[16px] text-[14px] font-['MiSans_VF:Normal'] text-[rgba(0,0,0,0.88)] hover:bg-[rgba(0,0,0,0.04)] transition-colors"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="h-[32px] px-[24px] bg-[#ff4d4f] text-white rounded-[16px] text-[14px] font-['MiSans_VF:Medium'] hover:opacity-90 transition-opacity"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑知识库对话框 */}
      {editingKb && (
        <EditKnowledgeBaseModal
          isOpen={true}
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

export default DatasetList