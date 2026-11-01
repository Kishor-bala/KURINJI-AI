import React, { useState, useEffect } from 'react';
import { Database, Sparkles, BookOpen } from 'lucide-react';
import KurinjiLogo from './components/KurinjiLogo';
import DirectAudioBar from './components/DirectAudioBar';
import ModuleGrid from './components/ModuleGrid';
import LearningCardModal from './components/LearningCardModal';
import VocabularyManager from './components/VocabularyManager';

import initialModulesData from './data/learning_modules.json';

export default function App() {
  const [selectedLanguage, setSelectedLanguage] = useState('Badaga');
  const [modulesData, setModulesData] = useState(initialModulesData);
  const [selectedModuleId, setSelectedModuleId] = useState(null);
  const [activeCard, setActiveCard] = useState(null);
  const [showManager, setShowManager] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Sync with backend API
  useEffect(() => {
    fetch('/api/modules')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.modules && data.modules.length > 0) {
          setModulesData(data);
        }
      })
      .catch((err) => {
        console.warn('Using bundled curriculum data:', err);
      });
  }, []);

  const handleSelectCard = (card) => {
    setActiveCard(card);
  };

  // Modal navigation across cards
  const currentCards = selectedModuleId
    ? modulesData.cards.filter((c) => c.category === selectedModuleId)
    : modulesData.cards;

  const currentIdx = activeCard ? currentCards.findIndex((c) => c.id === activeCard.id) : -1;
  const hasPrev = currentIdx > 0;
  const hasNext = currentIdx >= 0 && currentIdx < currentCards.length - 1;

  const handleNextCard = () => {
    if (hasNext) setActiveCard(currentCards[currentIdx + 1]);
  };

  const handlePrevCard = () => {
    if (hasPrev) setActiveCard(currentCards[currentIdx - 1]);
  };

  return (
    <div className="learning-workspace-root">
      {/* Top Application Header */}
      <header className="primary-top-header">
        <div className="header-brand-wrap">
          <KurinjiLogo size={28} />
          <div className="header-brand-titles">
            <div className="title-row">
              <span className="brand-main-title">KURINJI</span>
              <span className="brand-stage-badge">Primary Learning Desk</span>
            </div>
            <span className="brand-subtitle">
              Indigenous Bridge System • Mother Tongue to Tamil & English (K-5)
            </span>
          </div>
        </div>

        <div className="header-actions-group">
          {/* Dialect Switcher */}
          <div className="dialect-selector-group">
            <button
              type="button"
              className={`dialect-btn ${selectedLanguage === 'Badaga' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('Badaga')}
            >
              Badaga
            </button>
            <button
              type="button"
              className={`dialect-btn ${selectedLanguage === 'Marwari' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('Marwari')}
            >
              Marwari
            </button>
          </div>

          {/* Full Database Archive Access */}
          <button
            type="button"
            className={`wordbank-toggle-btn ${showManager ? 'active' : ''}`}
            onClick={() => setShowManager(!showManager)}
            title="Browse verified database of 3,319 indigenous words"
          >
            <Database size={15} />
            <span>{showManager ? 'Learning Desk' : 'Wordbank (3,319)'}</span>
          </button>
        </div>
      </header>

      {/* Main Educational Workspace */}
      <main className="learning-main-content">
        {showManager ? (
          <VocabularyManager
            initialLanguage={selectedLanguage}
            onClose={() => setShowManager(false)}
          />
        ) : (
          <div className="learning-scroll-canvas">
            {/* Direct Voice Input & Quick Concept Search */}
            <div className="voice-input-strip">
              <DirectAudioBar
                onSelectCard={handleSelectCard}
                selectedLanguage={selectedLanguage}
              />
            </div>

            {/* Thematic Topics & Kindergarten Concept Cards */}
            <ModuleGrid
              modules={modulesData.modules}
              cards={modulesData.cards}
              selectedModuleId={selectedModuleId}
              onSelectModule={setSelectedModuleId}
              onSelectCard={handleSelectCard}
              selectedLanguage={selectedLanguage}
            />
          </div>
        )}
      </main>

      {/* Multi-Sensory Phonics Learning Card Modal */}
      {activeCard && (
        <LearningCardModal
          card={activeCard}
          onClose={() => setActiveCard(null)}
          onNext={handleNextCard}
          onPrev={handlePrevCard}
          hasPrev={hasPrev}
          hasNext={hasNext}
          selectedLanguage={selectedLanguage}
        />
      )}
    </div>
  );
}
