import React from 'react';

export default function ProgressBar({
  value = 0,
  max = 100,
  label = '',
  variant = 'primary',
  height = '8px',
  showPercentage = false,
  className = ''
}) {
  const percent = Math.min(100, Math.max(0, Math.round((value / max) * 100)));

  return (
    <div className={`progress-container ${className}`}>
      {(label || showPercentage) && (
        <div className="d-flex justify-content-between align-items-center mb-1 small">
          {label && <span className="text-muted fw-medium">{label}</span>}
          {showPercentage && <span className={`fw-bold text-${variant}`}>{percent}%</span>}
        </div>
      )}
      <div className="progress" style={{ height }}>
        <div
          className={`progress-bar bg-${variant}`}
          role="progressbar"
          style={{ width: `${percent}%` }}
          aria-valuenow={percent}
          aria-valuemin="0"
          aria-valuemax="100"
        ></div>
      </div>
    </div>
  );
}
