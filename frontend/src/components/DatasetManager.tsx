import React, { useState } from 'react'
import DatasetList from './DatasetList'
import KnowledgeBaseDetailPage from './KnowledgeBaseDetailPage'
import './DatasetManager.css'

interface DatasetManagerProps {
  onClose?: () => void
  onNavigateToKBDetail?: (kbId: string, kbName: string) => void
}

const DatasetManager: React.FC<DatasetManagerProps> = ({ onNavigateToKBDetail }) => {
  const [currentView, setCurrentView] = useState<'list' | 'kb-detail'>('list')
  const [selectedKB, setSelectedKB] = useState<{ id: string; name: string } | null>(null)

  const handleSelectKB = (kbId: string, kbName: string) => {
    // 如果提供了导航函数，使用全局导航
    if (onNavigateToKBDetail) {
      onNavigateToKBDetail(kbId, kbName)
    } else {
      // 否则在内部切换视图
      setSelectedKB({ id: kbId, name: kbName })
      setCurrentView('kb-detail')
    }
  }

  const handleBackToList = () => {
    setCurrentView('list')
    setSelectedKB(null)
  }

  return (
    <div className="flex-1 flex flex-col">
      {currentView === 'list' ? (
        <DatasetList onSelectKB={handleSelectKB} />
      ) : currentView === 'kb-detail' && selectedKB ? (
        <div className="flex-1 overflow-hidden">
          <KnowledgeBaseDetailPage
            kbId={selectedKB.id}
            kbName={selectedKB.name}
            onBack={handleBackToList}
          />
        </div>
      ) : null}
    </div>
  )
}

export default DatasetManager