import React, { useState, useRef } from 'react';
import { uploadMaterial } from '../../services/api';

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png'];
const MAX_FILE_SIZE_MB = 25;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export default function UploadDropzone({ currentLevel, onUploadSuccess, onError }) {
  const [file, setFile] = useState(null);
  const [level, setLevel] = useState(currentLevel || 'A1');
  const [topic, setTopic] = useState('General');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const fileInputRef = useRef(null);

  const validateFile = (selectedFile) => {
    if (!selectedFile) return false;
    const name = selectedFile.name.toLowerCase();
    const hasValidExt = SUPPORTED_EXTENSIONS.some((ext) => name.endsWith(ext));
    if (!hasValidExt) {
      onError(`Unsupported file type. Supported types: ${SUPPORTED_EXTENSIONS.join(', ')}`);
      return false;
    }
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      onError(`File exceeds maximum size of ${MAX_FILE_SIZE_MB}MB.`);
      return false;
    }
    return true;
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        if (!title) {
          setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const picked = e.target.files[0];
      if (validateFile(picked)) {
        setFile(picked);
        if (!title) {
          setTitle(picked.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  };

  const handleReset = () => {
    setFile(null);
    setTitle('');
    setDescription('');
    setProgress(0);
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      onError('Please choose or drop a file first.');
      return;
    }

    setUploading(true);
    setProgress(5);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('cefr_level', level);
    formData.append('topic', topic);
    if (title.trim()) formData.append('title', title.trim());
    if (description.trim()) formData.append('description', description.trim());

    try {
      const res = await uploadMaterial(formData, (percent) => {
        setProgress(percent);
      });
      handleReset();
      onUploadSuccess(res);
    } catch (err) {
      console.error('Upload failed:', err);
      onError(err.response?.data?.detail || err.message || 'File upload failed');
      setUploading(false);
    }
  };

  return (
    <div className="card shadow-sm border-0 mb-4 bg-white">
      <div className="card-body p-4">
        <h5 className="card-title fw-bold mb-3 d-flex align-items-center gap-2">
          <i className="bi bi-cloud-arrow-up-fill text-primary"></i>
          Upload German Study Materials
        </h5>
        <p className="text-muted small mb-4">
          Upload PDF textbooks, DOCX notes, TXT vocab lists, or handwritten note images (.png, .jpg).
        </p>

        <form onSubmit={handleSubmit}>
          {/* Dropzone */}
          <div
            className={`dropzone-container mb-3 ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="d-none"
              accept=".pdf,.docx,.txt,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <i className="bi bi-file-earmark-arrow-up dropzone-icon d-block"></i>
            {file ? (
              <div>
                <strong className="text-primary d-block fs-6">{file.name}</strong>
                <span className="badge bg-secondary-subtle text-dark mt-1">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </span>
                <p className="text-muted small mt-2 mb-0">Click or drop another file to replace</p>
              </div>
            ) : (
              <div>
                <span className="fw-semibold text-dark d-block">
                  Drag and drop your German file here
                </span>
                <span className="text-muted small">or click to browse your computer</span>
                <div className="mt-2">
                  <span className="badge bg-light text-muted border me-1">PDF</span>
                  <span className="badge bg-light text-muted border me-1">DOCX</span>
                  <span className="badge bg-light text-muted border me-1">TXT</span>
                  <span className="badge bg-light text-muted border me-1">PNG / JPG</span>
                  <span className="text-muted small ms-1">(Max {MAX_FILE_SIZE_MB}MB)</span>
                </div>
              </div>
            )}
          </div>

          {/* Form Options */}
          <div className="row g-3">
            <div className="col-md-3">
              <label className="form-label small fw-semibold">Target Level</label>
              <select
                className="form-select form-select-sm"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                disabled={uploading}
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
                disabled={uploading}
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

            <div className="col-md-6">
              <label className="form-label small fw-semibold">Title (Optional)</label>
              <input
                type="text"
                className="form-control form-control-sm"
                placeholder="e.g., A1 Akkusativ & Dativ Exercises"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={uploading}
              />
            </div>

            <div className="col-12">
              <label className="form-label small fw-semibold">Notes / Description (Optional)</label>
              <input
                type="text"
                className="form-control form-control-sm"
                placeholder="Short note about what this material covers"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={uploading}
              />
            </div>
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div className="mt-3">
              <div className="d-flex justify-content-between small text-muted mb-1">
                <span>Uploading and extracting text...</span>
                <span>{progress}%</span>
              </div>
              <div className="progress" style={{ height: '8px' }}>
                <div
                  className="progress-bar progress-bar-striped progress-bar-animated bg-primary"
                  role="progressbar"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Submit Actions */}
          <div className="d-flex justify-content-end gap-2 mt-3">
            {file && !uploading && (
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={handleReset}
              >
                Clear
              </button>
            )}
            <button
              type="submit"
              className="btn btn-sm btn-primary px-3"
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                  Processing...
                </>
              ) : (
                <>
                  <i className="bi bi-upload me-1"></i>
                  Upload & Extract
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
