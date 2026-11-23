import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import LibraryPage from './pages/LibraryPage';
import NotesPage from './pages/NotesPage';
import QuestionBankPage from './pages/QuestionBankPage';
import LessonsPage from './pages/LessonsPage';
import LessonDetailPage from './pages/LessonDetailPage';
import VocabularyPage from './pages/VocabularyPage';
import GermanLevelsPage from './pages/GermanLevelsPage';
import PracticeReadingPage from './pages/PracticeReadingPage';
import PracticeListeningPage from './pages/PracticeListeningPage';
import PracticeWritingPage from './pages/PracticeWritingPage';
import PracticeSpeakingPage from './pages/PracticeSpeakingPage';
import TutorPage from './pages/TutorPage';
import ProgressPage from './pages/ProgressPage';
import SettingsPage from './pages/SettingsPage';
import AuthPage from './pages/AuthPage';
import { getHealth, getDashboardSummary, updateLearnerLevel, getCurrentUser, refreshCsrfToken, logout } from './services/api';

export default function App() {
  const location = useLocation();
  const previousPath = useRef(location.pathname);
  const [summary, setSummary] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [currentLevel, setCurrentLevel] = useState('A1');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mongoUnavailable, setMongoUnavailable] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(undefined);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then(async (user) => {
        await refreshCsrfToken();
        if (active) setCurrentUser(user);
      })
      .catch(() => { if (active) setCurrentUser(null); });
    return () => { active = false; };
  }, []);

  const fetchData = useCallback(async () => {
    if (!currentUser) return;
    setLoading(true);
    setError(null);
    setMongoUnavailable(false);
    try {
      const [healthResult, dashboardResult] = await Promise.allSettled([getHealth(), getDashboardSummary()]);
      const healthRes = healthResult.status === 'fulfilled' ? healthResult.value : null;
      if (dashboardResult.status === 'rejected') throw dashboardResult.reason;
      const dashRes = dashboardResult.value;

      setHealthStatus(healthRes);
      if (healthRes?.database?.status !== 'connected') {
        setMongoUnavailable(true);
      }

      setSummary(dashRes);
      if (dashRes?.current_level) {
        setCurrentLevel(dashRes.current_level);
      }
    } catch (err) {
      console.error('Error connecting to backend:', err);
      setSummary(null);
      const isDbErr = err.response?.status === 503 || err.message?.includes('Database');
      if (isDbErr) {
        setMongoUnavailable(true);
      }
      setError(err.response?.data?.detail || err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    if (currentUser) fetchData();
  }, [fetchData, currentUser]);

  useEffect(() => {
    const isOnSummaryPage = ['/', '/progress'].includes(location.pathname);
    const routeChanged = previousPath.current !== location.pathname;
    previousPath.current = location.pathname;
    // Refresh persisted summary data whenever the learner returns to a summary
    // page after completing an action elsewhere in the app.
    if (isOnSummaryPage && routeChanged) {
      fetchData();
    }
  }, [location.pathname, fetchData]);

  const handleLevelChange = async (newLevel) => {
    try {
      await updateLearnerLevel(newLevel);
      setCurrentLevel(newLevel);
      await fetchData();
    } catch (err) {
      console.error('Failed to change level:', err);
      alert('Failed to update level: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleLogout = async () => {
    try { await logout(); } finally { setCurrentUser(null); }
  };

  if (currentUser === undefined) {
    return <div className="min-vh-100 d-flex align-items-center justify-content-center text-muted">Checking your session…</div>;
  }
  if (!currentUser) {
    return <AuthPage onAuthenticated={setCurrentUser} />;
  }

  return (
    <div className="layout-wrapper">
      <Sidebar
        currentLevel={currentLevel}
        isOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
      />
      <div className="main-content">
        <Header
          currentLevel={currentLevel}
          onLevelChange={handleLevelChange}
          healthStatus={healthStatus}
          onRefresh={fetchData}
          loading={loading}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          onLogout={handleLogout}
        />
        <main className="content-body">
          <Routes>
            {/* 1. Dashboard */}
            <Route
              path="/"
              element={
                <Dashboard
                  summary={summary}
                  loading={loading}
                  error={error}
                  mongoUnavailable={mongoUnavailable}
                  onRefresh={fetchData}
                  onLevelChange={handleLevelChange}
                />
              }
            />

            {/* 2. My Library */}
            <Route
              path="/library"
              element={<LibraryPage currentLevel={currentLevel} summary={summary} onRefreshDashboard={fetchData} />}
            />
            <Route path="/notes" element={<NotesPage />} />
            <Route path="/question-bank" element={<QuestionBankPage />} />

            {/* 3. Curriculum & Lessons (Phase 3) */}
            <Route
              path="/lessons"
              element={<LessonsPage currentLevel={currentLevel} />}
            />
            <Route
              path="/lessons/:lessonId"
              element={<LessonDetailPage />}
            />

            {/* 4. Vocabulary Deck (Phase 3) */}
            <Route
              path="/vocabulary"
              element={<VocabularyPage currentLevel={currentLevel} />}
            />

            {/* 5. German Levels */}
            <Route
              path="/levels"
              element={<GermanLevelsPage currentLevel={currentLevel} onLevelChange={handleLevelChange} />}
            />

            {/* 4. Lesen (Reading) */}
            <Route
              path="/lesen"
              element={<PracticeReadingPage currentLevel={currentLevel} />}
            />
            <Route
              path="/practice/reading"
              element={<Navigate to="/lesen" replace />}
            />

            {/* 5. Hören (Listening) */}
            <Route
              path="/hoeren"
              element={<PracticeListeningPage currentLevel={currentLevel} />}
            />
            <Route
              path="/practice/listening"
              element={<Navigate to="/hoeren" replace />}
            />

            {/* 6. Schreiben (Writing) */}
            <Route
              path="/schreiben"
              element={<PracticeWritingPage currentLevel={currentLevel} />}
            />
            <Route
              path="/practice/writing"
              element={<Navigate to="/schreiben" replace />}
            />

            {/* 7. Sprechen (Speaking) */}
            <Route
              path="/sprechen"
              element={<PracticeSpeakingPage currentLevel={currentLevel} />}
            />
            <Route
              path="/practice/speaking"
              element={<Navigate to="/sprechen" replace />}
            />

            {/* 8. AI Tutor */}
            <Route
              path="/tutor"
              element={<TutorPage currentLevel={currentLevel} healthStatus={healthStatus} />}
            />

            {/* 9. Progress */}
            <Route
              path="/progress"
              element={<ProgressPage summary={summary} currentLevel={currentLevel} loading={loading} error={error} onRefresh={fetchData} />}
            />

            {/* 10. Settings */}
            <Route
              path="/settings"
              element={<SettingsPage healthStatus={healthStatus} onRefresh={fetchData} />}
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </div>
  );
}
