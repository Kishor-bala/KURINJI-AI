import React, { useState, useEffect } from 'react';
import { Plus, Search, ArrowLeft, Volume2, Check, RefreshCw } from 'lucide-react';

export default function VocabularyManager({ onClose, initialLanguage }) {
  const [language, setLanguage] = useState(initialLanguage || 'Badaga');
  const [search, setSearch] = useState('');
  const [vocabList, setVocabList] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  // Form states
  const [newWordId, setNewWordId] = useState('');
  const [newTamil, setNewTamil] = useState('');
  const [newEnglish, setNewEnglish] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [formMsg, setFormMsg] = useState('');

  const fetchVocabulary = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/vocabulary?language=${language}&limit=300`);
      const data = await res.json();
      setVocabList(data.entries || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load vocabulary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVocabulary();
  }, [language]);

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setFormMsg('');
    try {
      const res = await fetch('/api/vocabulary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          word_id: newWordId,
          language: language,
          tamil_meaning: newTamil,
          english_meaning: newEnglish,
          notes: newNotes,
        }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setFormMsg('Word added successfully!');
        setNewWordId('');
        setNewTamil('');
        setNewEnglish('');
        setNewNotes('');
        setShowAddForm(false);
        fetchVocabulary();
      } else {
        setFormMsg('Failed to add entry.');
      }
    } catch (err) {
      setFormMsg('Error: ' + err.message);
    }
  };

  const filteredEntries = vocabList.filter((item) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      item.word_id.toLowerCase().includes(q) ||
      (item.english_meaning && item.english_meaning.toLowerCase().includes(q)) ||
      (item.tamil_meaning && item.tamil_meaning.includes(q))
    );
  });

  return (
    <div className="vocab-manager-view">
      <div className="manager-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="nav-link-btn" onClick={onClose} title="Back to Voice Recognition">
            <ArrowLeft size={18} /> Back
          </button>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Vocabulary Management</h2>
        </div>

        <button
          className="analyse-button"
          style={{ width: 'auto', padding: '8px 16px', margin: 0, fontSize: '0.85rem' }}
          onClick={() => setShowAddForm(!showAddForm)}
        >
          <Plus size={16} /> {showAddForm ? 'Cancel' : 'Add Verified Word'}
        </button>
      </div>

      {showAddForm && (
        <form
          onSubmit={handleAddSubmit}
          style={{
            background: 'var(--bg-subtle)',
            padding: '20px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '24px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
          }}
        >
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Word ID (e.g. BDG_W0999)
            </label>
            <input
              type="text"
              required
              placeholder="BDG_W0999"
              value={newWordId}
              onChange={(e) => setNewWordId(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                marginTop: '4px',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Tamil Meaning
            </label>
            <input
              type="text"
              required
              placeholder="தமிழ் பொருள்"
              value={newTamil}
              onChange={(e) => setNewTamil(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                marginTop: '4px',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              English Meaning
            </label>
            <input
              type="text"
              required
              placeholder="English translation"
              value={newEnglish}
              onChange={(e) => setNewEnglish(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                marginTop: '4px',
              }}
            />
          </div>

          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <button
              type="submit"
              className="analyse-button"
              style={{ width: 'auto', padding: '8px 20px', margin: 0 }}
            >
              Save Verified Entry
            </button>
          </div>
          {formMsg && (
            <p style={{ gridColumn: '1 / -1', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {formMsg}
            </p>
          )}
        </form>
      )}

      {/* Language Switch & Search Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div className="lang-selector">
          <button
            className={`lang-btn ${language === 'Badaga' ? 'active' : ''}`}
            onClick={() => setLanguage('Badaga')}
          >
            Badaga ({language === 'Badaga' ? total : ''})
          </button>
          <button
            className={`lang-btn ${language === 'Marwari' ? 'active' : ''}`}
            onClick={() => setLanguage('Marwari')}
          >
            Marwari ({language === 'Marwari' ? total : ''})
          </button>
        </div>

        <div style={{ position: 'relative', width: '240px' }}>
          <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-light)' }} />
          <input
            type="text"
            placeholder="Search word or meaning..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 34px',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-color)',
              fontSize: '0.85rem',
            }}
          />
        </div>
      </div>

      <div className="table-wrapper">
        <table className="vocab-table">
          <thead>
            <tr>
              <th>Word ID</th>
              <th>Tamil Meaning</th>
              <th>English Meaning</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredEntries.map((row) => (
              <tr key={row.word_id}>
                <td>
                  <code>{row.word_id}</code>
                </td>
                <td className="tamil-text" style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  {row.tamil_meaning}
                </td>
                <td>{row.english_meaning}</td>
                <td>
                  <span style={{ color: 'var(--success-text)', fontSize: '0.75rem', fontWeight: 600 }}>
                    Verified
                  </span>
                </td>
              </tr>
            ))}
            {filteredEntries.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading vocabulary...' : 'No entries found.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
