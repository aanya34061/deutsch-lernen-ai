import React from 'react';

export default function AlertMessage({ type = 'info', title, message, onRetry, dismissible = false, onDismiss }) {
  const iconMap = {
    info: 'bi-info-circle-fill text-info',
    success: 'bi-check-circle-fill text-success',
    warning: 'bi-exclamation-triangle-fill text-warning',
    danger: 'bi-exclamation-octagon-fill text-danger',
  };

  return (
    <div className={`alert alert-${type} d-flex align-items-center justify-content-between p-3 rounded-3 shadow-sm mb-4`} role="alert">
      <div className="d-flex align-items-center gap-2">
        <i className={`bi ${iconMap[type] || 'bi-info-circle-fill'} fs-5`}></i>
        <div>
          {title && <strong className="d-block mb-0">{title}</strong>}
          <span className="small">{message}</span>
        </div>
      </div>
      <div className="d-flex align-items-center gap-2">
        {onRetry && (
          <button className={`btn btn-sm btn-outline-${type}`} onClick={onRetry}>
            Retry
          </button>
        )}
        {dismissible && onDismiss && (
          <button type="button" className="btn-close" aria-label="Close" onClick={onDismiss}></button>
        )}
      </div>
    </div>
  );
}
