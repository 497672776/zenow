import React, { useState, useEffect } from 'react'
import DocumentsTable from './DocumentsTable'
import FileUploadDialog from './FileUploadDialog'
import EditKnowledgeBaseModal from './EditKnowledgeBaseModal'
import Toast from './Toast'

import kbIcon5 from '../assets/kb-icon-5.svg'
import deleteIcon from '../assets/delete-icon.svg'
import editIcon from '../assets/edit-icon.svg'
import './KnowledgeBaseDetailPage.css'

interface KnowledgeBaseDetailPageProps {
  kbId: string
  kbName: string
  onBack?: () => void
  onSwitchToImageView?: () => void
}

interface KBInfo {
  name: string
  description: string
  avatarUrl?: string
  docCount: number
  totalSize: number
  updatedAt: string
}

const KnowledgeBaseDetailPage: React.FC<KnowledgeBaseDetailPageProps> = ({
  kbId,
  kbName,
  onBack,
  onSwitchToImageView,
}) => {
  const [refreshCount, setRefreshCount] = useState(0)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'warning' | 'success' | 'info' } | null>(null)
  const [showMenu, setShowMenu] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [hasImages, setHasImages] = useState(false)
  const [kbInfo, setKbInfo] = useState<KBInfo>({
    name: kbName,
    description: '',
    avatarUrl: undefined,
    docCount: 0,
    totalSize: 0,
    updatedAt: '昨天'
  })

  useEffect(() => {
    loadKBInfo()
  }, [kbId, refreshCount])

  // 格式化相对时间
  const formatRelativeTime = (isoString: string): string => {
    if (!isoString) return '未知'

    try {
      const normalizedDateString = isoString && !isoString.endsWith('Z') && isoString.includes('T')
        ? `${isoString}Z`
        : isoString

      const updatedDate = new Date(normalizedDateString)

      if (isNaN(updatedDate.getTime())) {
        console.warn('Invalid date string:', isoString)
        return isoString
      }

      const now = new Date()
      const diffMs = now.getTime() - updatedDate.getTime()
      const diffMinutes = Math.floor(diffMs / (1000 * 60))
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

      if (diffMinutes < 1) return '刚刚'
      if (diffMinutes < 60) return `${diffMinutes}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays === 1) return '昨天'
      if (diffDays <= 6) return `${diffDays}天前`
      if (diffDays <= 30) return '上周'
      if (diffDays <= 365) return '上月'
      return '去年'
    } catch (error) {
      console.error('Error formatting relative time:', isoString, error)
      return isoString
    }
  }

  const loadKBInfo = async () => {
    try {
      // TODO: 替换为实际的API调用
      const mockKbInfo = {
        name: kbName,
        description: '这是一个示例知识库的描述',
        avatarUrl: undefined,
        docCount: 5,
        totalSize: 1024000,
        updatedAt: formatRelativeTime(new Date().toISOString())
      }

      setKbInfo(mockKbInfo)

      // 检查是否有图片
      await checkForImages()
    } catch (error) {
      console.error('Failed to load KB info:', error)
    }
  }

  // 检查知识库是否包含图片
  const checkForImages = async () => {
    try {
      // TODO: 替换为实际的API调用
      // 模拟检查结果
      const hasAnyImages = false
      setHasImages(hasAnyImages)

      if (hasAnyImages) {
        console.log(`✅ KB "${kbName}" contains images, showing image view button`)
      }
    } catch (error) {
      console.error('Failed to check for images:', error)
      setHasImages(false)
    }
  }

  const handleUploadSuccess = () => {
    setShowUploadDialog(false)
    setRefreshCount(prev => prev + 1)
  }

  const handleUploadClick = async () => {
    try {
      // TODO: 检查llama-server配置
      setShowUploadDialog(true)
    } catch (error) {
      console.error('Failed to check llama-server configuration:', error)
      setToast({
        message: '无法验证 llama-server 配置',
        type: 'error'
      })
    }
  }

  const handleDeleteKB = () => {
    setDeleteConfirm(true)
    setShowMenu(false)
  }

  const confirmDeleteKB = async () => {
    setDeleteConfirm(false)

    try {
      // TODO: 替换为实际的API调用
      console.log(`删除知识库: ${kbName}`)

      setToast({
        message: '知识库已删除',
        type: 'success'
      })
      setTimeout(() => onBack?.(), 1500)
    } catch (error) {
      console.error('Failed to delete KB:', error)
      setToast({
        message: '删除失败',
        type: 'error'
      })
    }
  }

  const cancelDeleteKB = () => {
    setDeleteConfirm(false)
  }

  const handleEditSuccess = () => {
    setShowEditModal(false)
    setRefreshCount(prev => prev + 1)
  }

  return (
    <>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast(null)}
        />
      )}
      <div className="flex flex-col h-full bg-white overflow-hidden">
        {/* 主容器 - 分为左右两部分 */}
        <div className="flex-1 flex overflow-hidden">
          {/* 左侧 - 文件列表 */}
          <div className="flex-1 flex flex-col overflow-hidden min-w-0">
            <DocumentsTable
              kbId={kbId}
              kbName={kbName}
              refreshCount={refreshCount}
              onDocumentDeleted={() => setRefreshCount(prev => prev + 1)}
            />
          </div>

          {/* 右侧 - 知识库信息面板 (360px) */}
          <aside className="w-[360px] bg-[#f9f9fa] border-l border-[rgba(0,0,0,0.04)] flex flex-col flex-shrink-0 overflow-y-auto">
            {/* More 菜单 */}
            <div className="absolute right-8 top-20 z-50">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1.5 hover:bg-[rgba(0,0,0,0.04)] rounded-[8px] transition-colors"
                title="更多操作"
              >
                <span className="text-xl">⋮</span>
              </button>

              {showMenu && (
                <div className="absolute right-0 top-10 bg-white border border-[rgba(0,0,0,0.1)] rounded-[10px] shadow-lg min-w-[160px]">
                  <button
                    onClick={() => {
                      setShowMenu(false)
                      setShowEditModal(true)
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2 text-left text-black font-['MiSans_VF:Regular'] text-[14px] hover:bg-[rgba(0,0,0,0.04)] rounded-t-[8px] first:rounded-t-[8px]"
                  >
                    <img src={editIcon} alt="edit" className="w-4 h-4" />
                    <span>编辑</span>
                  </button>
                  <button
                    onClick={() => {
                      setShowMenu(false)
                      handleDeleteKB()
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2 text-left text-[#ff4d4f] font-['MiSans_VF:Regular'] text-[14px] hover:bg-[rgba(0,0,0,0.04)] rounded-b-[8px] last:rounded-b-[8px]"
                  >
                    <img src={deleteIcon} alt="delete" className="w-4 h-4" />
                    <span>删除知识库</span>
                  </button>
                </div>
              )}
            </div>

            {/* 内容 - 分为上下两部分 */}
            <div className="flex flex-col flex-1 p-8">
              {/* 上面 - 信息部分 */}
              <div className="flex flex-col items-center text-center">
                {/* Avatar */}
                <div className="w-[76px] h-[76px] rounded-[38px] overflow-hidden flex items-center justify-center mb-8 flex-shrink-0">
                  <img
                    src={kbInfo.avatarUrl || kbIcon5}
                    alt={kbInfo.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* 名称和描述 */}
                <div className="w-[296px] mb-8">
                  <h2 className="text-[20px] font-['MiSans_VF:Demibold'] text-black mb-2">
                    {kbInfo.name}
                  </h2>
                  {kbInfo.description && (
                    <p className="text-[14px] font-['MiSans_VF:Normal'] text-[rgba(0,0,0,0.5)] line-clamp-2">
                      {kbInfo.description}
                    </p>
                  )}
                </div>

                {/* 统计数据 - 两列布局 */}
                <div className="w-[296px] flex gap-12 justify-center">
                  <div className="flex flex-col items-center">
                    <span className="text-[16px] font-['MiSans_VF:Demibold'] text-[#6dce0b]">
                      {kbInfo.docCount}
                    </span>
                    <span className="text-[10px] font-['MiSans_VF:Light'] text-[rgba(0,0,0,0.5)]">
                      文件数量
                    </span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-[16px] font-['MiSans_VF:Demibold'] text-[#6dce0b]">
                      {kbInfo.updatedAt}
                    </span>
                    <span className="text-[10px] font-['MiSans_VF:Light'] text-[rgba(0,0,0,0.5)]">
                      最后更新
                    </span>
                  </div>
                </div>
              </div>

              {/* 下面 - 操作按钮 */}
              <div className="flex flex-col items-center mt-auto">
                <div className="w-[296px] space-y-3">
                  {/* 添加资料按钮 */}
                  <button
                    onClick={handleUploadClick}
                    className="w-full h-[40px] border border-[rgba(0,0,0,0.04)] text-black font-['MiSans_VF:Medium'] text-[14px] rounded-[32px] hover:bg-[rgba(0,0,0,0.04)] transition-colors"
                  >
                    添加资料
                  </button>

                  {/* 图片视图按钮 - 仅当有图片时显示 */}
                  {hasImages && onSwitchToImageView && (
                    <button
                      onClick={onSwitchToImageView}
                      className="w-full h-[40px] bg-[#b0e237] hover:bg-[#9ed020] text-black font-['MiSans_VF:Medium'] text-[13px] rounded-[32px] transition-colors flex items-center justify-center gap-2"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                      </svg>
                      图片视图
                    </button>
                  )}

                  {/* 返回按钮 */}
                  {onBack && (
                    <button
                      onClick={onBack}
                      className="w-full h-[40px] bg-gray-100 hover:bg-gray-200 text-black font-['MiSans_VF:Medium'] text-[14px] rounded-[32px] transition-colors"
                    >
                      返回列表
                    </button>
                  )}
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* 上传对话框 */}
        {showUploadDialog && (
          <FileUploadDialog
            kbName={kbName}
            onSuccess={handleUploadSuccess}
            onClose={() => setShowUploadDialog(false)}
          />
        )}

        {/* 编辑知识库对话框 */}
        <EditKnowledgeBaseModal
          isOpen={showEditModal}
          kbName={kbName}
          initialName={kbInfo.name}
          initialDescription={kbInfo.description}
          initialAvatarUrl={kbInfo.avatarUrl}
          onClose={() => setShowEditModal(false)}
          onSuccess={handleEditSuccess}
        />

        {/* 删除知识库确认对话框 */}
        {deleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-[12px] shadow-[0px_6px_16px_0px_rgba(0,0,0,0.08),0px_3px_6px_-4px_rgba(0,0,0,0.12),0px_9px_28px_8px_rgba(0,0,0,0.05)] w-[360px] overflow-hidden relative">
              {/* Header */}
              <div className="flex items-center justify-between px-[24px] pt-[20px] pb-[8px]">
                <h3 style={{ fontWeight: 600 }} className="text-[16px] text-[rgba(0,0,0,0.88)]">
                  删除知识库
                </h3>
                <button
                  onClick={cancelDeleteKB}
                  className="p-1 hover:bg-[rgba(0,0,0,0.04)] rounded-[4px] transition-colors"
                  title="关闭"
                >
                  <span className="text-lg">✕</span>
                </button>
              </div>

              {/* Content */}
              <div className="px-[24px] pt-0 pb-[16px]">
                <p className="text-[14px] font-['MiSans_VF:Normal'] text-[rgba(0,0,0,0.88)]">
                  您即将永久删除该知识库 <span className="font-['MiSans_VF:Medium']">"{kbName}"</span>，且无法恢复
                </p>
              </div>

              {/* Footer */}
              <div className="flex gap-[8px] items-center justify-end px-[24px] py-[20px]">
                <button
                  onClick={cancelDeleteKB}
                  className="h-[32px] px-[24px] border border-[rgba(0,0,0,0.1)] bg-white rounded-[16px] text-[14px] font-['MiSans_VF:Normal'] text-[rgba(0,0,0,0.88)] hover:bg-[rgba(0,0,0,0.04)] transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={confirmDeleteKB}
                  className="h-[32px] px-[24px] bg-[#ff4d4f] text-white rounded-[16px] text-[14px] font-['MiSans_VF:Medium'] hover:opacity-90 transition-opacity"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

export default KnowledgeBaseDetailPage