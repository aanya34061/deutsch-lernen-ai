import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getVocabulary, createVocabulary, updateVocabulary, deleteVocabulary } from '../services/api';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';
import { speakGerman } from '../utils/speech';

export default function VocabularyPage({ currentLevel }) {
  const [vocabList, setVocabList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [groupBy, setGroupBy] = useState('none'); // 'none' | 'topic' | 'level'

  // Add Word Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newWord, setNewWord] = useState({
    word: '',
    article: '',
    plural: '',
    meaning_en: '',
    example_de: '',
    example_en: '',
    cefr_level: currentLevel || 'A1',
    topic: 'General',
    status: 'learning',
  });
  const [saving, setSaving] = useState(false);

  const fetchVocabulary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (levelFilter) params.level = levelFilter;
      if (topicFilter) params.topic = topicFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await getVocabulary(params);
      setVocabList(data || []);
    } catch (err) {
      console.error('Failed to load vocabulary:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load vocabulary deck.');
    } finally {
      setLoading(false);
    }
  }, [search, levelFilter, topicFilter, statusFilter]);

  useEffect(() => {
    fetchVocabulary();
  }, [fetchVocabulary]);

  const handleStatusChange = async (vocabId, newStatus) => {
    try {
      await updateVocabulary(vocabId, { status: newStatus });
      setVocabList((prev) =>
        prev.map((item) => (item.id === vocabId || item._id === vocabId ? { ...item, status: newStatus } : item))
      );
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Could not update status: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (vocabId, wordText) => {
    if (!window.confirm(`Delete "${wordText}" from your vocabulary?`)) return;
    try {
      await deleteVocabulary(vocabId);
      setVocabList((prev) => prev.filter((item) => item.id !== vocabId && item._id !== vocabId));
      setSuccessMsg(`Deleted "${wordText}".`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Failed to delete vocabulary:', err);
      alert('Could not delete word: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!newWord.word.trim() || !newWord.meaning_en.trim()) {
      alert('Please provide both the German word and English translation.');
      return;
    }

    try {
      setSaving(true);
      await createVocabulary(newWord);
      setShowAddModal(false);
      setNewWord({
        word: '',
        article: '',
        plural: '',
        meaning_en: '',
        example_de: '',
        example_en: '',
        cefr_level: currentLevel || 'A1',
        topic: 'General',
        status: 'learning',
      });
      setSuccessMsg(`Added "${newWord.word}" to your vocabulary deck!`);
      setTimeout(() => setSuccessMsg(null), 3500);
      fetchVocabulary();
    } catch (err) {
      console.error('Failed to create vocabulary:', err);
      alert('Failed to save word: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // Grouping helper
  const groupedData = {};
  if (groupBy === 'topic') {
    vocabList.forEach((v) => {
      const key = v.topic || 'General';
      if (!groupedData[key]) groupedData[key] = [];
      groupedData[key].push(v);
    });
  } else if (groupBy === 'level') {
    vocabList.forEach((v) => {
      const key = v.cefr_level || 'A1';
      if (!groupedData[key]) groupedData[key] = [];
      groupedData[key].push(v);
    });
  }

  return (
    <div className="container-fluid p-0">
      {/* Page Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          <h3 className="fw-bold mb-1">
            <i className="bi bi-translate text-primary me-2"></i>
            German Vocabulary Deck
          </h3>
          <p className="text-muted mb-0">
            Study German words with articles (der, die, das), plurals, examples, and learning statuses.
          </p>
        </div>
        <div className="d-flex gap-2">
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => setShowAddModal(true)}
          >
            <i className="bi bi-plus-circle me-1"></i> Add Word Manually
          </button>
          <Link to="/lessons" className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-journal-bookmark me-1"></i> Lessons
          </Link>
        </div>
      </div>

      {successMsg && (
        <AlertMessage
          type="success"
          message={successMsg}
          dismissible
          onDismiss={() => setSuccessMsg(null)}
        />
      )}

      {error && (
        <AlertMessage
          type="danger"
          message={error}
          onRetry={fetchVocabulary}
          dismissible
          onDismiss={() => setError(null)}
        />
      )}

      {/* Filter and Search Bar */}
      <div className="card shadow-sm border-0 bg-white mb-4">
        <div className="card-body p-3">
          <div className="row g-2 align-items-center">
            {/* Search Input */}
            <div className="col-lg-4 col-md-6">
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light text-muted border-end-0">
                  <i className="bi bi-search"></i>
                </span>
                <input
                  type="text"
                  className="form-control border-start-0"
                  placeholder="Search German words or English meanings..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                {search && (
                  <button className="btn btn-outline-secondary" onClick={() => setSearch('')}>
                    <i className="bi bi-x"></i>
                  </button>
                )}
              </div>
            </div>

            {/* Level Filter */}
            <div className="col-lg-2 col-md-3 col-6">
              <select
                className="form-select form-select-sm"
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
              >
                <option value="">All Levels</option>
                <option value="A1">Level A1</option>
                <option value="A2">Level A2</option>
                <option value="B1">Level B1</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="col-lg-2 col-md-3 col-6">
              <select
                className="form-select form-select-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="new">New</option>
                <option value="learning">Learning</option>
                <option value="mastered">Mastered</option>
              </select>
            </div>

            {/* Group By Filter */}
            <div className="col-lg-2 col-md-4 col-6">
              <select
                className="form-select form-select-sm"
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value)}
              >
                <option value="none">No Grouping</option>
                <option value="topic">Group by Topic</option>
                <option value="level">Group by CEFR Level</option>
              </select>
            </div>

            {/* Reset Filters */}
            <div className="col-lg-2 col-md-4 col-6 text-end">
              {(search || levelFilter || topicFilter || statusFilter || groupBy !== 'none') && (
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => {
                    setSearch('');
                    setLevelFilter('');
                    setTopicFilter('');
                    setStatusFilter('');
                    setGroupBy('none');
                  }}
                >
                  <i className="bi bi-x-circle me-1"></i> Reset Filters
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Vocabulary Items View */}
      {loading ? (
        <LoadingState message="Loading your German vocabulary cards..." />
      ) : vocabList.length === 0 ? (
        <div className="card shadow-sm border-0 p-5 text-center bg-white rounded-3">
          <i className="bi bi-translate display-4 text-muted mb-3 d-block"></i>
          <h5 className="fw-bold">No vocabulary words found</h5>
          <p className="text-muted small mb-4">
            Add words manually or save key vocabulary while studying German lessons!
          </p>
          <div>
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={() => setShowAddModal(true)}
            >
              <i className="bi bi-plus-circle me-1"></i> Add First Word
            </button>
          </div>
        </div>
      ) : groupBy !== 'none' ? (
        Object.entries(groupedData).map(([groupKey, items], idx) => (
          <div key={idx} className="mb-4">
            <h5 className="fw-bold text-dark mb-3">
              <i className="bi bi-folder2-open text-primary me-2"></i>
              {groupKey} ({items.length})
            </h5>
            <div className="row g-3">
              {items.map((v) => renderVocabCard(v, handleStatusChange, handleDelete))}
            </div>
          </div>
        ))
      ) : (
        <div className="row g-3">
          {vocabList.map((v) => renderVocabCard(v, handleStatusChange, handleDelete))}
        </div>
      )}

      {/* Add Word Modal */}
      {showAddModal && (
        <>
          <div className="modal-backdrop-custom" onClick={() => !saving && setShowAddModal(false)}></div>
          <div className="modal-custom d-flex align-items-center justify-content-center p-3" tabIndex="-1">
            <div className="modal-dialog w-100" style={{ maxWidth: '540px' }}>
              <div className="modal-content shadow-lg border-0 rounded-3">
                <div className="modal-header bg-light py-3 border-bottom">
                  <h5 className="modal-title fw-bold text-dark">
                    <i className="bi bi-plus-circle text-primary me-2"></i>
                    Add Vocabulary Word
                  </h5>
                  <button
                    type="button"
                    className="btn-close"
                    aria-label="Close"
                    disabled={saving}
                    onClick={() => setShowAddModal(false)}
                  ></button>
                </div>
                <form onSubmit={handleAddSubmit}>
                  <div className="modal-body p-4">
                    <div className="row g-3 mb-3">
                      <div className="col-md-4">
                        <label className="form-label small fw-semibold">Article (if noun)</label>
                        <select
                          className="form-select form-select-sm"
                          value={newWord.article}
                          onChange={(e) => setNewWord({ ...newWord, article: e.target.value })}
                        >
                          <option value="">None (Verb/Adj)</option>
                          <option value="der">der (Masculine)</option>
                          <option value="die">die (Feminine)</option>
                          <option value="das">das (Neuter)</option>
                        </select>
                      </div>

                      <div className="col-md-8">
                        <label className="form-label small fw-semibold">
                          German Word <span className="text-danger">*</span>
                        </label>
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          placeholder="e.g., Apfel, Buch, sprechen"
                          value={newWord.word}
                          onChange={(e) => setNewWord({ ...newWord, word: e.target.value })}
                          required
                        />
                      </div>
                    </div>

                    <div className="row g-3 mb-3">
                      <div className="col-md-6">
                        <label className="form-label small fw-semibold">
                          English Translation <span className="text-danger">*</span>
                        </label>
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          placeholder="e.g., apple, book, to speak"
                          value={newWord.meaning_en}
                          onChange={(e) => setNewWord({ ...newWord, meaning_en: e.target.value })}
                          required
                        />
                      </div>

                      <div className="col-md-6">
                        <label className="form-label small fw-semibold">Plural Form (Optional)</label>
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          placeholder="e.g., die Äpfel, die Bücher"
                          value={newWord.plural}
                          onChange={(e) => setNewWord({ ...newWord, plural: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="row g-3 mb-3">
                      <div className="col-md-6">
                        <label className="form-label small fw-semibold">CEFR Level</label>
                        <select
                          className="form-select form-select-sm"
                          value={newWord.cefr_level}
                          onChange={(e) => setNewWord({ ...newWord, cefr_level: e.target.value })}
                        >
                          <option value="A1">A1</option>
                          <option value="A2">A2</option>
                          <option value="B1">B1</option>
                        </select>
                      </div>

                      <div className="col-md-6">
                        <label className="form-label small fw-semibold">Topic</label>
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          placeholder="e.g., Food, Travel, School"
                          value={newWord.topic}
                          onChange={(e) => setNewWord({ ...newWord, topic: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="mb-3">
                      <label className="form-label small fw-semibold">Example Sentence (German)</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="e.g., Ich esse einen roten Apfel."
                        value={newWord.example_de}
                        onChange={(e) => setNewWord({ ...newWord, example_de: e.target.value })}
                      />
                    </div>

                    <div className="mb-2">
                      <label className="form-label small fw-semibold">Example Translation (English)</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="e.g., I am eating a red apple."
                        value={newWord.example_en}
                        onChange={(e) => setNewWord({ ...newWord, example_en: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="modal-footer bg-light py-2 border-top d-flex justify-content-end gap-2">
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={() => setShowAddModal(false)}
                      disabled={saving}
                    >
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-sm btn-primary" disabled={saving}>
                      {saving ? 'Saving...' : 'Add Word'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Single Card View helper
function renderVocabCard(v, onStatusChange, onDelete) {
  const vocabId = v.id || v._id;
  const articleClass =
    v.article === 'der' ? 'badge-der' : v.article === 'die' ? 'badge-die' : v.article === 'das' ? 'badge-das' : 'bg-light text-dark';

  return (
    <div key={vocabId} className="col-12 col-md-6 col-xl-4">
      <div className="card h-100 shadow-sm border-0 material-card bg-white">
        <div className="card-body p-3 d-flex flex-column">
          {/* Top badges */}
          <div className="d-flex justify-content-between align-items-center mb-2">
            <div className="d-flex align-items-center gap-1">
              {v.article && <span className={`badge ${articleClass} px-2 py-1`}>{v.article}</span>}
              <span className="badge bg-secondary-subtle text-dark" style={{ fontSize: '0.7rem' }}>
                {v.cefr_level || 'A1'}
              </span>
            </div>
            <div>
              {v.status === 'mastered' ? (
                <span className="badge bg-success-subtle text-success border border-success-subtle">
                  <i className="bi bi-star-fill me-1"></i> Mastered
                </span>
              ) : v.status === 'learning' ? (
                <span className="badge bg-primary-subtle text-primary border border-primary-subtle">
                  <i className="bi bi-arrow-repeat me-1"></i> Learning
                </span>
              ) : (
                <span className="badge bg-light text-secondary border">
                  New
                </span>
              )}
            </div>
          </div>

          {/* Word and Pronunciation */}
          <div className="d-flex justify-content-between align-items-start mb-1">
            <h5 className="fw-bold text-dark mb-0">{v.word}</h5>
            <button
              type="button"
              className="btn btn-sm btn-link text-primary p-0"
              onClick={() => speakGerman(v.word)}
              title="Listen to German pronunciation"
            >
              <i className="bi bi-volume-up fs-5"></i>
            </button>
          </div>

          {/* Meaning & Plural */}
          <div className="text-secondary small mb-2">
            <strong>{v.meaning_en}</strong>
            {v.plural && <span className="text-muted ms-2">(Pl: {v.plural})</span>}
          </div>

          {/* Example Sentence */}
          {v.example_de && (
            <div className="p-2 mb-2 bg-light rounded border small">
              <span className="text-dark d-block fw-medium">{v.example_de}</span>
              {v.example_en && <span className="text-muted small">{v.example_en}</span>}
            </div>
          )}

          {/* Footer Actions */}
          <div className="d-flex justify-content-between align-items-center pt-2 border-top mt-auto">
            <span className="badge bg-light text-muted border text-truncate" style={{ maxWidth: '110px' }}>
              {v.topic || 'General'}
            </span>
            <div className="btn-group btn-group-sm">
              {v.status !== 'mastered' ? (
                <button
                  type="button"
                  className="btn btn-outline-success"
                  onClick={() => onStatusChange(vocabId, 'mastered')}
                  title="Mark as Mastered"
                >
                  <i className="bi bi-check-lg"></i> Master
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => onStatusChange(vocabId, 'learning')}
                  title="Mark as Learning"
                >
                  <i className="bi bi-arrow-counterclockwise"></i> Review
                </button>
              )}
              <button
                type="button"
                className="btn btn-outline-danger"
                onClick={() => onDelete(vocabId, v.word)}
                title="Delete word"
              >
                <i className="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
