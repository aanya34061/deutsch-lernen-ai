import React, { useState } from 'react';
import { addLearningLink } from '../../services/api';

export default function AddLinkForm({ currentLevel, onLinkAdded, onError }) {
  const [url, setUrl] = useState('');
  const [level, setLevel] = useState(currentLevel || 'A1');
  const [topic, setTopic] = useState('General');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isYouTube = url.toLowerCase().includes('youtube.com') || url.toLowerCase().includes('youtu.be');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) {
      onError('Please enter a valid URL.');
      return;
    }

    try {
      setSubmitting(true);
      const res = await addLearningLink({
        url: url.trim(),
        cefr_level: level,
        topic: topic,
        title: title.trim() || undefined,
        description: description.trim() || undefined,
      });

      setUrl('');
      setTitle('');
      setDescription('');
      onLinkAdded(res);
    } catch (err) {
      console.error('Failed to add link:', err);
      onError(err.response?.data?.detail || err.message || 'Failed to add learning link');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card shadow-sm border-0 mb-4 bg-white">
      <div className="card-body p-4">
        <h5 className="card-title fw-bold mb-3 d-flex align-items-center gap-2">
          <i className="bi bi-link-45deg text-danger fs-4"></i>
          Add Learning Link (YouTube / Web)
        </h5>
        <p className="text-muted small mb-3">
          Add German YouTube video lessons or web articles. Transcripts and captions will be extracted automatically when accessible.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="row g-3">
            <div className="col-12">
              <label className="form-label small fw-semibold">
                Resource URL <span className="text-danger">*</span>
              </label>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light">
                  {isYouTube ? (
                    <i className="bi bi-youtube text-danger"></i>
                  ) : (
                    <i className="bi bi-globe text-primary"></i>
                  )}
                </span>
                <input
                  type="url"
                  className="form-control"
                  placeholder="https://www.youtube.com/watch?v=... or https://learngerman.dw.com/..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={submitting}
                  required
                />
              </div>
              {isYouTube && (
                <div className="form-text text-danger small mt-1">
                  <i className="bi bi-info-circle me-1"></i>
                  YouTube video detected. German/English captions will be extracted if available.
                </div>
              )}
            </div>

            <div className="col-md-3">
              <label className="form-label small fw-semibold">Target Level</label>
              <select
                className="form-select form-select-sm"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                disabled={submitting}
              >
                {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map((lvl) => (
                  <option key={lvl} value={lvl}>
                    {lvl} {lvl === currentLevel ? '(Active)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-md-3">
              <label className="form-label small fw-semibold">Topic / Skill</label>
              <select
                className="form-select form-select-sm"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={submitting}
              >
                <option value="General">General / Overview</option>
                <option value="Hören">Hören (Listening / Video)</option>
                <option value="Grammar">Grammar (Grammatik)</option>
                <option value="Vocabulary">Vocabulary (Wortschatz)</option>
                <option value="Lesen">Lesen (Reading)</option>
                <option value="Schreiben">Schreiben (Writing)</option>
                <option value="Sprechen">Sprechen (Speaking)</option>
              </select>
            </div>

            <div className="col-md-6">
              <label className="form-label small fw-semibold">Title (Optional)</label>
              <input
                type="text"
                className="form-control form-control-sm"
                placeholder="Leave blank to auto-detect title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={submitting}
              />
            </div>

            <div className="col-12">
              <label className="form-label small fw-semibold">Notes / Description (Optional)</label>
              <input
                type="text"
                className="form-control form-control-sm"
                placeholder="Key concepts or grammar rules discussed in this video/link"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>

          <div className="d-flex justify-content-end gap-2 mt-3">
            <button
              type="submit"
              className="btn btn-sm btn-danger px-3"
              disabled={!url.trim() || submitting}
            >
              {submitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                  Fetching & Indexing...
                </>
              ) : (
                <>
                  <i className="bi bi-plus-circle me-1"></i>
                  Add Learning Link
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
