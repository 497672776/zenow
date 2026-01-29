import { useState } from 'react'
import KnowledgeBaseOverviewPage from './KnowledgeBaseOverviewPage'
import KnowledgeBaseDetailPage from './KnowledgeBaseDetailPage'
import './KnowledgeBasePage.css'

function KnowledgeBasePage() {
  const [currentView, setCurrentView] = useState<'list' | 'kb-detail'>('list')
  const [selectedKB, setSelectedKB] = useState<{ id: string; name: string } | null>(null)

  const handleSelectKB = (kbId: string, kbName: string) => {
    setSelectedKB({ id: kbId, name: kbName })
    setCurrentView('kb-detail')
  }

  const handleBackToList = () => {
    setCurrentView('list')
    setSelectedKB(null)
  }

  return (
    <div className="knowledge-base-page">
      {currentView === 'list' ? (
        <KnowledgeBaseOverviewPage onSelectKB={handleSelectKB} />
      ) : currentView === 'kb-detail' && selectedKB ? (
        <KnowledgeBaseDetailPage
          kbId={selectedKB.id}
          kbName={selectedKB.name}
          onBack={handleBackToList}
        />
      ) : null}
    </div>
  )
}

export default KnowledgeBasePage
