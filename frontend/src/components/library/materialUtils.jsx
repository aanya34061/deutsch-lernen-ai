import React from 'react';
export * from './materialUtils.js';

export const getTypeIcon = (fileType = '') => {
  const type = fileType.toLowerCase();
  switch (type) {
    case 'pdf':
      return <i className="bi bi-file-earmark-pdf text-danger fs-5"></i>;
    case 'docx':
    case 'doc':
      return <i className="bi bi-file-earmark-word text-primary fs-5"></i>;
    case 'txt':
      return <i className="bi bi-file-earmark-text text-secondary fs-5"></i>;
    case 'image':
      return <i className="bi bi-file-earmark-image text-success fs-5"></i>;
    case 'youtube':
      return <i className="bi bi-youtube text-danger fs-5"></i>;
    case 'link':
      return <i className="bi bi-link-45deg text-info fs-5"></i>;
    case 'audio':
      return <i className="bi bi-file-earmark-music text-warning fs-5"></i>;
    default:
      return <i className="bi bi-file-earmark text-muted fs-5"></i>;
  }
};

export const getStatusBadge = (status = '') => {
  const s = status.toLowerCase();
  switch (s) {
    case 'ready':
      return (
        <span className="badge bg-success-subtle text-success border border-success-subtle">
          <i className="bi bi-check-circle-fill me-1"></i> Ready
        </span>
      );
    case 'processing':
      return (
        <span className="badge bg-primary-subtle text-primary border border-primary-subtle">
          <span className="spinner-border spinner-border-sm me-1" role="status" style={{ width: '0.7rem', height: '0.7rem' }}></span>
          Processing
        </span>
      );
    case 'uploaded':
      return (
        <span className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle">
          <i className="bi bi-clock-history me-1"></i> Uploaded
        </span>
      );
    case 'failed':
      return (
        <span className="badge bg-danger-subtle text-danger border border-danger-subtle">
          <i className="bi bi-exclamation-triangle-fill me-1"></i> Failed
        </span>
      );
    default:
      return <span className="badge bg-secondary">{status}</span>;
  }
};
