import React from 'react';

export default function LoadingState({ message = 'Loading German study materials...', size = 'md' }) {
  const spinnerClass = size === 'sm' ? 'spinner-border-sm' : '';
  return (
    <div className="text-center py-5">
      <div className={`spinner-border text-primary ${spinnerClass}`} role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
      <p className="mt-3 text-muted small fw-medium">{message}</p>
    </div>
  );
}
