import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTypeIcon, getTypeLabel, getStatusBadge, formatFileSize, formatDate } from './materialUtils.jsx';
import { getMaterialFileUrl, createLessonFromMaterial, extractVocabularyFromMaterial, batchCreateVocabulary } from '../../services/api';

export default function MaterialDetailModal({ material, onClose }) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [creatingLesson, setCreatingLesson] = useState(false);
  const [extractingVocab, setExtractingVocab] = useState(false);
  const [extractedItems, setExtractedItems] = useState(null);
  const [selectedWords, setSelectedWords] = useState(new Set());
  const [savingVocab, setSavingVocab] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);

  if (!material) return null;

  const isLink = material.source_type === 'link' || material.file_type === 'youtube' || material.file_type === 'link';
  const fileUrl = !isLink ? getMaterialFileUrl(material.id || material._id) : material.source_url;
  const text = material.extracted_text || '';
  const charCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const handleCreateLesson = async () => {
    try {
      setCreatingLesson(true);
      const res = await createLessonFromMaterial({
        material_id: material.id || material._id,
        title: `Study Session: ${material.title}`,
        cefr_level: material.cefr_level || 'A1',
        topic: material.topic || 'General',
      });
      setActionNotice({
        type: 'success',
        message: 'Study page created from the material’s extracted text.',
        lessonId: res.id || res._id,
      });
    } catch (err) {
      console.error('Failed to create lesson from material:', err);
      setActionNotice({
        type: 'danger',
        message: 'Failed to create lesson: ' + (err.response?.data?.detail || err.message),
      });
    } finally {
      setCreatingLesson(false);
    }
  };

  const handleExtractVocab = async () => {
    try {
      setExtractingVocab(true);
      const res = await extractVocabularyFromMaterial({
        material_id: material.id || material._id,
      });
      const items = res.items || [];
      setExtractedItems(items);
      setSelectedWords(new Set(items.map((_, i) => i)));
    } catch (err) {
      console.error('Failed to extract vocabulary:', err);
      alert('Could not extract vocabulary: ' + (err.response?.data?.detail || err.message));
    } finally {
      setExtractingVocab(false);
    }
  };

  const handleSaveSelectedVocab = async () => {
    if (!extractedItems) return;
    const toSave = extractedItems
      .filter((_, idx) => selectedWords.has(idx))
      .filter((item) => item.word.trim() && item.meaning_en.trim());

    if (toSave.length === 0) {
      alert('Please ensure selected items have both a German word and English translation.');
      return;
    }

    try {
      setSavingVocab(true);
      await batchCreateVocabulary({
        source_type: 'upload',
        source_id: material.id || material._id,
        source_title: material.title,
        words: toSave.map((item) => ({
          word: item.word,
          article: item.article || '',
          plural: item.plural || '',
          meaning_en: item.meaning_en,
          example_de: item.example_context,
          cefr_level: item.cefr_level || material.cefr_level || 'A1',
          topic: item.topic || material.topic || 'General',
          status: 'learning',
        })),
      });
      setActionNotice({
        type: 'success',
        message: `Saved ${toSave.length} vocabulary words to your deck!`,
      });
      setExtractedItems(null);
    } catch (err) {
      console.error('Failed to save vocabulary batch:', err);
      alert('Could not save vocabulary: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingVocab(false);
    }
  };

  return (
    <>
      <div className="modal-backdrop-custom" onClick={onClose}></div>
      <div className="modal-custom d-flex align-items-center justify-content-center p-3" tabIndex="-1">
        <div className="modal-dialog modal-lg modal-dialog-scrollable w-100" style={{ maxWidth: '850px' }}>
          <div className="modal-content shadow-lg border-0 rounded-3">
            {/* Modal Header */}
            <div className="modal-header bg-light py-3 border-bottom">
              <div className="d-flex align-items-center gap-2 overflow-hidden">
                {getTypeIcon(material.file_type)}
                <h5 className="modal-title fw-bold text-dark text-truncate" title={material.title}>
                  {material.title}
                </h5>
              </div>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
            </div>

            {/* Modal Body */}
            <div className="modal-body p-4">
              {/* Notifications */}
              {actionNotice && (
                <div className={`alert alert-${actionNotice.type} d-flex justify-content-between align-items-center mb-3 p-3 rounded`}>
                  <span>{actionNotice.message}</span>
                  {actionNotice.lessonId && (
                    <button
                      type="button"
                      className="btn btn-sm btn-success"
                      onClick={() => {
                        onClose();
                        navigate(`/lessons/${actionNotice.lessonId}`);
                      }}
                    >
                      Open Lesson <i className="bi bi-arrow-right ms-1"></i>
                    </button>
                  )}
                </div>
              )}

              {/* Badges and Metadata */}
              <div className="d-flex flex-wrap gap-2 align-items-center mb-3">
                {getStatusBadge(material.status)}
                <span className="badge bg-primary-subtle text-primary fw-semibold">
                  Level: {material.cefr_level || 'A1'}
                </span>
                <span className="badge bg-secondary-subtle text-dark">
                  Topic: {material.topic || 'General'}
                </span>
                <span className="badge bg-light text-secondary border text-uppercase">
                  Format: {getTypeLabel(material.file_type)}
                </span>
                {material.file_size > 0 && (
                  <span className="badge bg-light text-muted border">
                    Size: {formatFileSize(material.file_size)}
                  </span>
                )}
                {material.created_at && (
                  <span className="text-muted small ms-auto">
                    Added: {formatDate(material.created_at)}
                  </span>
                )}
              </div>

              {/* Description */}
              {material.description && (
                <div className="mb-3">
                  <h6 className="fw-semibold small text-muted text-uppercase mb-1">Description</h6>
                  <p className="small mb-0 text-dark bg-light p-2 rounded border">
                    {material.description}
                  </p>
                </div>
              )}

              {/* Source info */}
              {isLink && material.source_url && (
                <div className="mb-3">
                  <h6 className="fw-semibold small text-muted text-uppercase mb-1">Source URL</h6>
                  <a
                    href={material.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="small text-truncate d-block"
                  >
                    {material.source_url} <i className="bi bi-box-arrow-up-right ms-1"></i>
                  </a>
                </div>
              )}

              {/* Error Message if Failed */}
              {material.status === 'failed' && (
                <div className="alert alert-danger d-flex align-items-center gap-2 mb-3">
                  <i className="bi bi-exclamation-triangle-fill fs-5"></i>
                  <div>
                    <strong>Extraction Failed:</strong> {material.error_message || 'File could not be parsed.'}
                    <div className="small mt-1 text-muted">
                      Manual alternative: You can copy and paste notes or create custom vocabulary directly in the Vocabulary Deck.
                    </div>
                  </div>
                </div>
              )}

              {/* Learning Actions from Material (Phase 3 Integration) */}
              <div className="card bg-light border p-3 mb-4">
                <h6 className="fw-bold text-dark mb-2">
                  <i className="bi bi-mortarboard-fill text-primary me-2"></i>
                  Phase 3: Learn from this Material
                </h6>
                <div className="d-flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={handleCreateLesson}
                    disabled={creatingLesson || !text}
                    title="Create a study page that links to this material’s extracted text"
                  >
                    {creatingLesson ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                        Generating Lesson...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-book me-1"></i> Create Study Page
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary"
                    onClick={handleExtractVocab}
                    disabled={extractingVocab || !text}
                    title="Extract candidate German vocabulary words and review before saving"
                  >
                    {extractingVocab ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                        Scanning Words...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-translate me-1"></i> Extract & Review Vocabulary
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    className="btn btn-sm btn-outline-info"
                    onClick={() => {
                      onClose();
                      navigate(`/tutor?materialId=${material.id || material._id}`);
                    }}
                    disabled={!text}
                    title="Ask the AI Tutor questions grounded in this document"
                  >
                    <i className="bi bi-robot me-1"></i> Ask AI Tutor (RAG)
                  </button>
                </div>
              </div>

              {/* Vocabulary Extraction Review Panel */}
              {extractedItems && (
                <div className="card border-primary p-3 mb-4 bg-white shadow-sm">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <div>
                      <h6 className="fw-bold text-primary mb-0">
                        <i className="bi bi-ui-checks me-1"></i>
                        Review Extracted Vocabulary ({extractedItems.length} candidate words)
                      </h6>
                      <small className="text-muted">
                        Uncertain entries are flagged. Review translations and articles before saving.
                      </small>
                    </div>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => setExtractedItems(null)}
                    >
                      Close Review
                    </button>
                  </div>

                  <div className="table-responsive" style={{ maxHeight: '280px', overflowY: 'auto' }}>
                    <table className="table table-sm table-hover align-middle small mb-3">
                      <thead className="table-light">
                        <tr>
                          <th style={{ width: '35px' }}></th>
                          <th>Article</th>
                          <th>German Word</th>
                          <th>English Meaning</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {extractedItems.map((item, idx) => {
                          const isSelected = selectedWords.has(idx);
                          return (
                            <tr key={idx} className={item.is_uncertain ? 'table-warning' : ''}>
                              <td>
                                <input
                                  type="checkbox"
                                  className="form-check-input"
                                  checked={isSelected}
                                  onChange={(e) => {
                                    const next = new Set(selectedWords);
                                    if (e.target.checked) next.add(idx);
                                    else next.delete(idx);
                                    setSelectedWords(next);
                                  }}
                                />
                              </td>
                              <td style={{ width: '90px' }}>
                                <input
                                  type="text"
                                  className="form-control form-control-sm"
                                  value={item.article}
                                  placeholder="der/die/das"
                                  onChange={(e) => {
                                    const copy = [...extractedItems];
                                    copy[idx].article = e.target.value;
                                    setExtractedItems(copy);
                                  }}
                                />
                              </td>
                              <td>
                                <input
                                  type="text"
                                  className="form-control form-control-sm fw-bold"
                                  value={item.word}
                                  onChange={(e) => {
                                    const copy = [...extractedItems];
                                    copy[idx].word = e.target.value;
                                    setExtractedItems(copy);
                                  }}
                                />
                              </td>
                              <td>
                                <input
                                  type="text"
                                  className="form-control form-control-sm"
                                  value={item.meaning_en}
                                  placeholder="Enter English translation..."
                                  onChange={(e) => {
                                    const copy = [...extractedItems];
                                    copy[idx].meaning_en = e.target.value;
                                    setExtractedItems(copy);
                                  }}
                                />
                              </td>
                              <td>
                                {item.is_uncertain ? (
                                  <span className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle" title={item.review_note}>
                                    Needs Review
                                  </span>
                                ) : (
                                  <span className="badge bg-success-subtle text-success border border-success-subtle">
                                    Verified
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="d-flex justify-content-end">
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      onClick={handleSaveSelectedVocab}
                      disabled={savingVocab || selectedWords.size === 0}
                    >
                      {savingVocab ? 'Saving to Deck...' : `Save ${selectedWords.size} Words to Vocabulary Deck`}
                    </button>
                  </div>
                </div>
              )}

              {/* Extracted Text Section */}
              <div className="d-flex justify-content-between align-items-center mb-2 mt-4">
                <h6 className="fw-bold mb-0 text-dark">
                  <i className="bi bi-file-text me-1 text-primary"></i>
                  Extracted Learning Content
                </h6>
                <div className="d-flex align-items-center gap-3">
                  <small className="text-muted">
                    {wordCount} words ({charCount} chars)
                  </small>
                  {text && (
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary py-1 px-2"
                      onClick={handleCopy}
                    >
                      {copied ? (
                        <>
                          <i className="bi bi-check2 text-success me-1"></i> Copied
                        </>
                      ) : (
                        <>
                          <i className="bi bi-clipboard me-1"></i> Copy Text
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>

              {text ? (
                <div className="extracted-text-viewer">
                  {text}
                </div>
              ) : (
                <div className="alert alert-secondary text-center py-4 mb-0">
                  <i className="bi bi-file-earmark-x fs-3 d-block text-muted mb-2"></i>
                  <span className="text-muted small">
                    No text could be extracted from this document.
                  </span>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="modal-footer bg-light py-2 border-top d-flex justify-content-between">
              <div>
                {isLink ? (
                  <a
                    href={material.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-sm btn-outline-primary"
                  >
                    <i className="bi bi-box-arrow-up-right me-1"></i> Visit Link
                  </a>
                ) : (
                  <a
                    href={fileUrl}
                    download
                    className="btn btn-sm btn-outline-primary"
                  >
                    <i className="bi bi-download me-1"></i> Download File
                  </a>
                )}
              </div>
              <button type="button" className="btn btn-sm btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
