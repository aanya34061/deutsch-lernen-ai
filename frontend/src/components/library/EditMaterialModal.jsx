import React, { useState } from 'react';
import { updateMaterial } from '../../services/api';

export default function EditMaterialModal({ material, onClose, onUpdated, onError }) {
  const [title, setTitle] = useState(material?.title || '');
  const [level, setLevel] = useState(material?.cefr_level || 'A1');
  const [topic, setTopic] = useState(material?.topic || 'General');
  const [description, setDescription] = useState(material?.description || '');
  const [saving, setSaving] = useState(false);

  if (!material) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      onError('Title cannot be empty.');
      return;
    }

    try {
      setSaving(true);
      const res = await updateMaterial(material.id || material._id, {
        title: title.trim(),
        cefr_level: level,
        topic: topic,
        description: description.trim() || undefined,
      });
      onUpdated(res);
      onClose();
    } catch (err) {
      console.error('Failed to update material:', err);
      onError(err.response?.data?.detail || err.message || 'Failed to update material');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <div className="modal-backdrop-custom" onClick={onClose}></div>
      <div className="modal-custom d-flex align-items-center justify-content-center p-3" tabIndex="-1">
        <div className="modal-dialog w-100" style={{ maxWidth: '550px' }}>
          <div className="modal-content shadow-lg border-0 rounded-3">
            <div className="modal-header bg-light py-3 border-bottom">
              <h5 className="modal-title fw-bold text-dark">
                <i className="bi bi-pencil-square text-primary me-2"></i>
                Edit Study Material
              </h5>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body p-4">
                <div className="mb-3">
                  <label className="form-label small fw-semibold">Title</label>
                  <input
                    type="text"
                    className="form-control"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={saving}
                    required
                  />
                </div>

                <div className="row g-3 mb-3">
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Target Level</label>
                    <select
                      className="form-select form-select-sm"
                      value={level}
                      onChange={(e) => setLevel(e.target.value)}
                      disabled={saving}
                    >
                      {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map((lvl) => (
                        <option key={lvl} value={lvl}>
                          {lvl}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Topic / Skill</label>
                    <select
                      className="form-select form-select-sm"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      disabled={saving}
                    >
                      <option value="General">General / Overview</option>
                      <option value="Grammar">Grammar (Grammatik)</option>
                      <option value="Vocabulary">Vocabulary (Wortschatz)</option>
                      <option value="Lesen">Lesen (Reading)</option>
                      <option value="Hören">Hören (Listening)</option>
                      <option value="Schreiben">Schreiben (Writing)</option>
                      <option value="Sprechen">Sprechen (Speaking)</option>
                    </select>
                  </div>
                </div>

                <div className="mb-2">
                  <label className="form-label small fw-semibold">Notes / Description</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    disabled={saving}
                    placeholder="Brief description or context"
                  ></textarea>
                </div>
              </div>

              <div className="modal-footer bg-light py-2 border-top d-flex justify-content-end gap-2">
                <button type="button" className="btn btn-sm btn-secondary" onClick={onClose} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-sm btn-primary" disabled={saving}>
                  {saving ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
