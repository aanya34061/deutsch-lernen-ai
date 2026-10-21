import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-white border-top py-3 px-4 text-center text-muted small mt-auto">
      <div className="container-fluid d-flex flex-column flex-sm-row justify-content-between align-items-center gap-2">
        <span>
          🇩🇪 <strong>DeutschLernen AI</strong> — Personal German Language Learning System
        </span>
        <span className="text-secondary">
          Note: App scores assist self-study and do not constitute official CEFR certification.
        </span>
      </div>
    </footer>
  );
}
