import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar({ currentLevel, isOpen, onClose }) {
  const mainNav = [
    { label: 'Dashboard', path: '/', icon: 'bi-grid-fill' },
    { label: 'Lessons', path: '/lessons', icon: 'bi-journal-bookmark-fill', badge: 'A1-B1' },
    { label: 'Vocabulary', path: '/vocabulary', icon: 'bi-translate' },
    { label: 'My Library', path: '/library', icon: 'bi-folder2-open' },
    { label: 'My Notes', path: '/notes', icon: 'bi-journal-text' },
    { label: 'Question Bank', path: '/question-bank', icon: 'bi-patch-question' },
    { label: 'German Levels', path: '/levels', icon: 'bi-bar-chart-steps', badge: 'A1-C2' },
  ];

  const skillNav = [
    { label: 'Lesen (Reading)', path: '/lesen', icon: 'bi-file-earmark-text', badge: 'Skill 1' },
    { label: 'Hören (Listening)', path: '/hoeren', icon: 'bi-headphones', badge: 'Skill 2' },
    { label: 'Schreiben (Writing)', path: '/schreiben', icon: 'bi-pencil-square', badge: 'Skill 3' },
    { label: 'Sprechen (Speaking)', path: '/sprechen', icon: 'bi-mic-fill', badge: 'Skill 4' },
    { label: 'AI Tutor', path: '/tutor', icon: 'bi-robot', badge: 'RAG AI' },
  ];

  const systemNav = [
    { label: 'Progress', path: '/progress', icon: 'bi-graph-up-arrow' },
    { label: 'Settings', path: '/settings', icon: 'bi-gear-fill' },
  ];

  const handleLinkClick = () => {
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="sidebar-backdrop d-lg-none"
          onClick={onClose}
          aria-hidden="true"
        ></div>
      )}

      {/* Sidebar Container */}
      <aside className={`sidebar p-3 ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Mobile Header with Close button */}
        <div className="d-flex d-lg-none justify-content-between align-items-center mb-3 pb-2 border-bottom">
          <span className="fw-bold text-primary">🇩🇪 DeutschLernen</span>
          <button className="btn btn-sm btn-outline-secondary" onClick={onClose} aria-label="Close sidebar">
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        {/* Current Active CEFR Badge */}
        <div className="mb-3 px-2">
          <div className="d-flex align-items-center justify-content-between p-2 rounded bg-light border">
            <div>
              <small className="text-uppercase text-muted fw-bold d-block" style={{ fontSize: '0.7rem' }}>
                Active Level
              </small>
              <strong className="text-primary">{currentLevel || 'A1'}</strong>
            </div>
            <span className="badge bg-primary px-2 py-1">Foundational</span>
          </div>
        </div>

        {/* Main Navigation */}
        <div className="nav flex-column mb-3">
          <small className="text-uppercase fw-bold text-muted px-2 mb-2" style={{ fontSize: '0.75rem' }}>
            Core
          </small>
          {mainNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              end={item.path === '/'}
              onClick={handleLinkClick}
            >
              <i className={`bi ${item.icon}`}></i>
              <span className="flex-grow-1">{item.label}</span>
              {item.badge && (
                <span className="badge bg-light text-muted border small" style={{ fontSize: '0.65rem' }}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        {/* Language Skills Navigation */}
        <div className="nav flex-column mb-3">
          <small className="text-uppercase fw-bold text-muted px-2 mb-2" style={{ fontSize: '0.75rem' }}>
            Language Skills
          </small>
          {skillNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              onClick={handleLinkClick}
            >
              <i className={`bi ${item.icon}`}></i>
              <span className="flex-grow-1">{item.label}</span>
              {item.badge && (
                <span className="badge bg-light text-dark border small" style={{ fontSize: '0.65rem' }}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        {/* System & Analytics Navigation */}
        <div className="nav flex-column mt-auto pt-2 border-top">
          {systemNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              onClick={handleLinkClick}
            >
              <i className={`bi ${item.icon}`}></i>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </aside>
    </>
  );
}
