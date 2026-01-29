import React, { useState, useEffect } from 'react'
import DocumentsTable from '../components/DocumentsTable'
import FileUploadDialog from '../components/FileUploadDialog'
import CreateKnowledgeBaseModal from '../components/CreateKnowledgeBaseModal'
import Toast from '../components/Toast'

import kbIcon5 from '../assets/kb-icon-5.png'
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
      <div className="knowledge-base-detail">
        {/* 主容器 - 分为左右两部分 */}
        <div className="kb-detail-container">
          {/* 左侧 - 文件列表 */}
          <div className="kb-detail-main">
            <DocumentsTable
              kbId={kbId}
              kbName={kbName}
              refreshCount={refreshCount}
              onDocumentDeleted={() => setRefreshCount(prev => prev + 1)}
            />
          </div>

          {/* 右侧 - 知识库信息面板 (360px) */}
          <aside className="kb-detail-sidebar">
            {/* More 菜单 */}
            <div className="kb-detail-menu">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="kb-detail-menu-button"
                title="更多操作"
              >
                <span style={{ fontSize: '20px' }}>⋮</span>
              </button>

              {showMenu && (
                <div className="kb-detail-menu-dropdown">
                  <button
                    onClick={() => {
                      setShowMenu(false)
                      setShowEditModal(true)
                    }}
                    className="kb-detail-menu-item"
                  >
                    <img src={editIcon} alt="edit" style={{ width: '16px', height: '16px' }} />
                    <span>编辑</span>
                  </button>
                  <button
                    onClick={() => {
                      setShowMenu(false)
                      handleDeleteKB()
                    }}
                    className="kb-detail-menu-item delete"
                  >
                    <img src={deleteIcon} alt="delete" style={{ width: '16px', height: '16px' }} />
                    <span>删除知识库</span>
                  </button>
                </div>
              )}
            </div>

            {/* 内容 - 分为上下两部分 */}
            <div className="kb-detail-content">
              {/* 上面 - 信息部分 */}
              <div >
                {/* Avatar */}
                <div className="kb-detail-avatar">
                  <img
                    src={kbInfo.avatarUrl || kbIcon5}
                    alt={kbInfo.name}

                  />
                </div>

                {/* 名称和描述 */}
                <div className="kb-detail-info">
                  <h2 className="kb-detail-name">
                    {kbInfo.name}
                  </h2>
                  {kbInfo.description && (
                    <p className="kb-detail-description">
                      {kbInfo.description}
                    </p>
                  )}
                </div>

                {/* 统计数据 - 两列布局 */}
                <div className="kb-detail-stats">
                  <div className="kb-detail-stat">
                    <span className="kb-detail-stat-value">
                      {kbInfo.docCount}
                    </span>
                    <span className="kb-detail-stat-label">
                      文件数量
                    </span>
                  </div>
                  <div className="kb-detail-stat">
                    <span className="kb-detail-stat-value">
                      {kbInfo.updatedAt}
                    </span>
                    <span className="kb-detail-stat-label">
                      最后更新
                    </span>
                  </div>
                </div>
              </div>

              {/* 下面 - 操作按钮 */}
              <div className="kb-detail-actions">
                <div className="kb-detail-actions-group">
                  {/* 添加资料按钮 */}
                  <button
                    onClick={handleUploadClick}
                    className="kb-detail-action-button secondary"
                  >
                    添加资料
                  </button>

                  {/* 图片视图按钮 - 仅当有图片时显示 */}
                  {hasImages && onSwitchToImageView && (
                    <button
                      onClick={onSwitchToImageView}
                      className="kb-detail-action-button primary"
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
                      className="kb-detail-action-button back"
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
        <CreateKnowledgeBaseModal
          isOpen={showEditModal}
          mode="edit"
          kbName={kbName}
          initialName={kbInfo.name}
          initialDescription={kbInfo.description}
          initialAvatarUrl={kbInfo.avatarUrl}
          onClose={() => setShowEditModal(false)}
          onSuccess={handleEditSuccess}
        />

        {/* 删除知识库确认对话框 */}
        {deleteConfirm && (
          <div className="delete-confirm-modal">
            <div className="delete-confirm-dialog">
              {/* Header */}
              <div className="delete-confirm-header">
                <h3 style={{ fontWeight: 600 }} className="delete-confirm-title">
                  删除知识库
                </h3>
                <button
                  onClick={cancelDeleteKB}
                  className="delete-confirm-close"
                  title="关闭"
                >
                  <span style={{ fontSize: '18px' }}>✕</span>
                </button>
              </div>

              {/* Content */}
              <div className="delete-confirm-content">
                <p style={{ fontSize: '14px', color: 'rgba(0,0,0,0.88)' }}>
                  您即将永久删除该知识库 <span className="font-['MiSans_VF:Medium']">"{kbName}"</span>，且无法恢复
                </p>
              </div>

              {/* Footer */}
              <div className="delete-confirm-footer">
                <button
                  onClick={cancelDeleteKB}
                  className="delete-confirm-button cancel"
                >
                  取消
                </button>
                <button
                  onClick={confirmDeleteKB}
                  className="delete-confirm-button delete"
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
