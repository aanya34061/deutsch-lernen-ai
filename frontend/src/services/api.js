import axios from 'axios';

const API_ORIGIN = import.meta.env.VITE_API_ORIGIN?.replace(/\/$/, '');
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (API_ORIGIN ? `${API_ORIGIN}/api/v1` : '/api/v1');
let csrfToken = null;

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  if (csrfToken && !['get', 'head', 'options'].includes((config.method || 'get').toLowerCase())) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

export const getCurrentUser = async () => (await api.get('/auth/me')).data;
export const refreshCsrfToken = async () => {
  const result = (await api.get('/auth/csrf')).data;
  csrfToken = result.csrf_token;
  return csrfToken;
};
export const authenticate = async (endpoint, credentials) => {
  const result = (await api.post(`/auth/${endpoint}`, credentials)).data;
  csrfToken = result.csrf_token;
  return result;
};
export const logout = async () => {
  await api.post('/auth/logout');
  csrfToken = null;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getLevels = async () => {
  const response = await api.get('/levels');
  return response.data;
};

export const getLevelDetail = async (code) => {
  const response = await api.get(`/levels/${code}`);
  return response.data;
};

export const getDashboardSummary = async () => {
  const response = await api.get('/dashboard');
  return response.data;
};

export const updateLearnerLevel = async (cefr_level) => {
  const response = await api.post('/dashboard/level', { cefr_level });
  return response.data;
};

// ==================== Study Library (Phase 2) ====================

export const getMaterials = async (params = {}) => {
  const response = await api.get('/library', { params });
  return response.data;
};

export const getMaterial = async (materialId) => {
  const response = await api.get(`/library/${materialId}`);
  return response.data;
};

export const uploadMaterial = async (formData, onProgress) => {
  const response = await api.post('/library/upload', formData, {
    timeout: 120000,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
  return response.data;
};

export const addLearningLink = async (linkData) => {
  const response = await api.post('/library/links', linkData);
  return response.data;
};

export const updateMaterial = async (materialId, updateData) => {
  const response = await api.patch(`/library/${materialId}`, updateData);
  return response.data;
};

export const deleteMaterial = async (materialId) => {
  const response = await api.delete(`/library/${materialId}`);
  return response.data;
};

export const retryMaterialProcessing = async (materialId) => {
  const response = await api.post(`/library/${materialId}/process/retry`);
  return response.data;
};

export const getStudyNotes = async (materialId) => {
  const response = await api.get('/study/notes', { params: materialId ? { material_id: materialId } : {} });
  return response.data;
};

export const saveStudyNote = async (noteId, markdown) => {
  const response = await api.put(`/study/notes/${noteId}`, { markdown });
  return response.data;
};

export const regenerateStudyNote = async (noteId) => {
  const response = await api.post(`/study/notes/${noteId}/regenerate`);
  return response.data;
};

export const deleteStudyNote = async (noteId) => {
  const response = await api.delete(`/study/notes/${noteId}`);
  return response.data;
};

export const getStudyQuestions = async (params = {}) => {
  const response = await api.get('/study/questions', { params });
  return response.data;
};

export const getMaterialFileUrl = (materialId) => {
  return `${API_BASE_URL}/library/${materialId}/file`;
};

// ==================== Lessons & Curriculum (Phase 3) ====================

export const getLessons = async (params = {}) => {
  const response = await api.get('/lessons', { params });
  return response.data;
};

export const getLesson = async (lessonId) => {
  const response = await api.get(`/lessons/${lessonId}`);
  return response.data;
};

export const markLessonCompleted = async (lessonId) => {
  const response = await api.post(`/lessons/${lessonId}/complete`);
  return response.data;
};

export const createLessonFromMaterial = async (data) => {
  const response = await api.post('/lessons/from-material', data);
  return response.data;
};

// ==================== Practice Engine & Exercises (Phase 3) ====================

export const getExercise = async (exerciseId) => {
  const response = await api.get(`/exercises/${exerciseId}`);
  return response.data;
};

export const submitExercise = async (exerciseId, userAnswer) => {
  const response = await api.post(`/exercises/${exerciseId}/submit`, { user_answer: userAnswer });
  return response.data;
};

// ==================== Vocabulary Management (Phase 3) ====================

export const getVocabulary = async (params = {}) => {
  const response = await api.get('/vocabulary', { params });
  return response.data;
};

export const createVocabulary = async (vocabData) => {
  const response = await api.post('/vocabulary', vocabData);
  return response.data;
};

export const batchCreateVocabulary = async (batchData) => {
  const response = await api.post('/vocabulary/batch', batchData);
  return response.data;
};

export const updateVocabulary = async (vocabId, updateData) => {
  const response = await api.patch(`/vocabulary/${vocabId}`, updateData);
  return response.data;
};

export const deleteVocabulary = async (vocabId) => {
  const response = await api.delete(`/vocabulary/${vocabId}`);
  return response.data;
};

export const extractVocabularyFromMaterial = async (reqData) => {
  const response = await api.post('/vocabulary/extract-from-material', reqData);
  return response.data;
};

// ==================== AI German Tutor & RAG (Phase 4) ====================

export const getTutorStatus = async () => {
  const response = await api.get('/tutor/status');
  return response.data;
};

export const sendTutorMessage = async (chatData) => {
  // Local model inference can take longer than the default API timeout,
  // especially on its first request while Ollama loads the model.
  const response = await api.post('/tutor/chat', chatData, { timeout: 210000 });
  return response.data;
};

export const getTutorConversations = async (userId) => {
  const response = await api.get('/tutor/conversations', { params: userId ? { user_id: userId } : {} });
  return response.data;
};

export const getTutorConversation = async (conversationId) => {
  const response = await api.get(`/tutor/conversations/${conversationId}`);
  return response.data;
};

export const deleteTutorConversation = async (conversationId) => {
  const response = await api.delete(`/tutor/conversations/${conversationId}`);
  return response.data;
};

export const generateTutorExercises = async (data) => {
  // Local models can take a while to produce and validate a question set.
  const response = await api.post('/tutor/exercises/generate', data, { timeout: 210000 });
  return response.data;
};

export const getIndexStatus = async () => {
  const response = await api.get('/tutor/index/status');
  return response.data;
};

export const rebuildIndex = async (force = false) => {
  const response = await api.post('/tutor/index/rebuild', null, { params: { force } });
  return response.data;
};

export const retryMaterialIndex = async (materialId) => {
  const response = await api.post(`/tutor/index/retry/${materialId}`);
  return response.data;
};

// ==================== Interactive German Skills Practice (Phase 5) ====================

// 1. Lesen (Reading)
export const getReadingExercises = async (params = {}) => {
  const response = await api.get('/practice/reading', { params });
  return response.data;
};

export const getReadingExercise = async (exerciseId) => {
  const response = await api.get(`/practice/reading/${exerciseId}`);
  return response.data;
};

export const submitReadingAnswers = async (exerciseId, answers, timeSpentSeconds = null) => {
  const response = await api.post(`/practice/reading/${exerciseId}/submit`, {
    answers,
    time_spent_seconds: timeSpentSeconds
  });
  return response.data;
};

// 2. Hören (Listening)
export const getListeningExercises = async (params = {}) => {
  const response = await api.get('/practice/listening', { params });
  return response.data;
};

export const getListeningExercise = async (exerciseId) => {
  const response = await api.get(`/practice/listening/${exerciseId}`);
  return response.data;
};

export const submitListeningAnswers = async (exerciseId, answers, timeSpentSeconds = null) => {
  const response = await api.post(`/practice/listening/${exerciseId}/submit`, {
    answers,
    time_spent_seconds: timeSpentSeconds
  });
  return response.data;
};

export const getListeningResources = async (params = {}) => {
  const response = await api.get('/practice/listening/resources', { params });
  return response.data;
};

export const completeListeningResource = async (resourceId) => {
  const response = await api.post(`/practice/listening/resources/${encodeURIComponent(resourceId)}/complete`);
  return response.data;
};

// 3. Schreiben (Writing)
export const getWritingPrompts = async (params = {}) => {
  const response = await api.get('/practice/writing/prompts', { params });
  return response.data;
};

export const getWritingPrompt = async (promptId) => {
  const response = await api.get(`/practice/writing/prompts/${promptId}`);
  return response.data;
};

export const getWritingDraft = async (promptId) => {
  const response = await api.get(`/practice/writing/drafts/${promptId}`);
  return response.data;
};

export const saveWritingDraft = async (draftData) => {
  const response = await api.post('/practice/writing/drafts', draftData);
  return response.data;
};

export const deleteWritingDraft = async (draftId) => {
  const response = await api.delete(`/practice/writing/drafts/${draftId}`);
  return response.data;
};

export const evaluateWriting = async (submissionData) => {
  const response = await api.post('/practice/writing/evaluate', submissionData);
  return response.data;
};

export const getWritingSubmissions = async (params = {}) => {
  const response = await api.get('/practice/writing/submissions', { params });
  return response.data;
};

// 4. Sprechen (Speaking)
export const getSpeakingScenarios = async (params = {}) => {
  const response = await api.get('/practice/speaking/scenarios', { params });
  return response.data;
};

export const startSpeakingSession = async (sessionData) => {
  const response = await api.post('/practice/speaking/sessions', sessionData);
  return response.data;
};

export const getSpeakingSession = async (sessionId) => {
  const response = await api.get(`/practice/speaking/sessions/${sessionId}`);
  return response.data;
};

export const sendSpeakingMessage = async (sessionId, message, audioUrl = null) => {
  const response = await api.post(`/practice/speaking/sessions/${sessionId}/message`, {
    message,
    audio_url: audioUrl
  });
  return response.data;
};

// 5. Practice Progress
export const getPracticeProgress = async () => {
  const response = await api.get('/practice/progress');
  return response.data;
};

export default api;
