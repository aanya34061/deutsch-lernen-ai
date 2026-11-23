import React, { useState, useRef } from 'react';
import { uploadMaterial } from '../../services/api';

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png'];
const MAX_FILE_SIZE_MB = import.meta.env.PROD ? 4 : 25;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export default function UploadDropzone({ onUploadSuccess, onError }) {
  const [files, setFiles] = useState([]);
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

  const addFiles = (incomingFiles) => {
    const selected = Array.from(incomingFiles || []);
    if (!selected.length) return;

    const validFiles = selected.filter(validateFile);
    const combined = [...files, ...validFiles];
    const uniqueFiles = combined.filter((item, index, all) =>
      all.findIndex((candidate) => candidate.name === item.name && candidate.size === item.size && candidate.lastModified === item.lastModified) === index
    );

    if (uniqueFiles.length > 1 && uniqueFiles.some((item) => !/\.(jpe?g|png)$/i.test(item.name))) {
      onError('Select multiple pictures together, or upload a single PDF, DOCX, or TXT file.');
      return;
    }
    setFiles(uniqueFiles);
    const previousAutoTitle = files.length === 1 ? files[0].name.replace(/\.[^/.]+$/, '') : '';
    if (uniqueFiles.length > 1 && title && title === previousAutoTitle) {
      setTitle('');
    } else if (!title && uniqueFiles.length === 1) {
      setTitle(uniqueFiles[0].name.replace(/\.[^/.]+$/, ''));
    }
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
    addFiles(e.dataTransfer.files);
  };

  const handleFileChange = (e) => {
    addFiles(e.target.files);
    e.target.value = '';
  };

  const handleReset = () => {
    setFiles([]);
    setTitle('');
    setDescription('');
    setProgress(0);
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!files.length) {
      onError('Please choose or drop at least one file first.');
      return;
    }

    setUploading(true);
    setProgress(5);
    const uploadedMaterials = [];
    const failedUploads = [];

    for (const [index, selectedFile] of files.entries()) {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const baseTitle = title.trim();
      const fileTitle = selectedFile.name.replace(/\.[^/.]+$/, '');
      if (baseTitle) formData.append('title', files.length > 1 ? `${baseTitle} — ${fileTitle}` : baseTitle);
      if (description.trim()) formData.append('description', description.trim());

      try {
        const result = await uploadMaterial(formData, (percent) => {
          setProgress(Math.round(((index + percent / 100) / files.length) * 100));
        });
        uploadedMaterials.push(result);
        setProgress(Math.round(((index + 1) / files.length) * 100));
      } catch (err) {
        console.error(`Upload failed for ${selectedFile.name}:`, err);
        failedUploads.push({ file: selectedFile, message: err.response?.data?.detail || err.message || 'Upload failed.' });
      }
    }
    setProgress(100);

    if (uploadedMaterials.length) {
      onUploadSuccess(uploadedMaterials, failedUploads.map(({ file, message }) => `${file.name}: ${message}`));
    }
    if (failedUploads.length) {
      setUploading(false);
      setFiles(failedUploads.map(({ file }) => file));
      onError(`Uploaded ${uploadedMaterials.length} of ${files.length} files. Failed: ${failedUploads.map(({ file }) => file.name).join(', ')}. You can retry the remaining files.`);
    } else if (uploadedMaterials.some((material) => material.status === 'failed')) {
      setUploading(false);
      onError('The pictures were uploaded, but some could not be processed. Retry processing from the library.');
    } else {
      handleReset();
    }
  };

  return (
    <div className="card shadow-sm border-0 mb-4 bg-white">
      <div className="card-body p-4">
        <h5 className="card-title fw-bold mb-3 d-flex align-items-center gap-2">
          <i className="bi bi-cloud-arrow-up-fill text-primary"></i>
          Upload a file
        </h5>
        <p className="text-muted small mb-4">
          Upload one PDF, DOCX, or TXT file, or select several handwritten note pictures (.png, .jpg) together.
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
              multiple
              onClick={(event) => event.stopPropagation()}
              onChange={handleFileChange}
              disabled={uploading}
            />
            <i className="bi bi-file-earmark-arrow-up dropzone-icon d-block"></i>
            {files.length ? (
              <div>
                <strong className="text-primary d-block fs-6">{files.length} file{files.length === 1 ? '' : 's'} selected</strong>
                <ul className="list-unstyled small mt-2 mb-0">
                  {files.map((selectedFile, index) => (
                    <li key={`${selectedFile.name}-${selectedFile.lastModified}`} className="d-flex align-items-center justify-content-center gap-2">
                      <span>{selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)</span>
                      {!uploading && (
                        <button
                          type="button"
                          className="btn btn-sm btn-link text-danger p-0"
                          aria-label={`Remove ${selectedFile.name}`}
                          onClick={(event) => {
                            event.stopPropagation();
                            setFiles((current) => current.filter((_, fileIndex) => fileIndex !== index));
                          }}
                        >
                          <i className="bi bi-x-circle" />
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
                {!uploading && <p className="text-muted small mt-2 mb-0">Click or drop more files to add them</p>}
              </div>
            ) : (
              <div>
                <span className="fw-semibold text-dark d-block">
                  Drag and drop German files or pictures here
                </span>
                <span className="text-muted small">or click to browse your computer</span>
                <div className="mt-2">
                  <span className="badge bg-light text-muted border me-1">PDF</span>
                  <span className="badge bg-light text-muted border me-1">DOCX</span>
                  <span className="badge bg-light text-muted border me-1">TXT</span>
                  <span className="badge bg-light text-muted border me-1">PNG / JPG</span>
                  <span className="text-muted small ms-1">(Max {MAX_FILE_SIZE_MB}MB each; multi-select is for pictures)</span>
                </div>
              </div>
            )}
          </div>

          <div className="row g-3">
            <div className="col-12">
              <label className="form-label small fw-semibold">Title or title prefix (Optional)</label>
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
            {files.length > 0 && !uploading && (
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
              disabled={!files.length || uploading}
            >
              {uploading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                  Processing...
                </>
              ) : (
                <>
                  <i className="bi bi-upload me-1"></i>
                  Upload {files.length > 1 ? `${files.length} Pictures` : '& Extract'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
