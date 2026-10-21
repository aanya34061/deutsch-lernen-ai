/**
 * Native Web Speech API helpers for German pronunciation (TTS)
 * and German speech recognition (STT).
 * 100% free, private, and runs locally in the browser without paid cloud APIs.
 */

export const hasSpeechSynthesis = () => {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
};

export const hasGermanVoice = () => {
  if (!hasSpeechSynthesis()) return false;
  const voices = window.speechSynthesis.getVoices();
  return voices.some(v => v.lang === 'de-DE' || v.lang.startsWith('de'));
};

export const getGermanVoice = () => {
  if (!hasSpeechSynthesis()) return null;
  const voices = window.speechSynthesis.getVoices();
  return (
    voices.find(v => v.lang === 'de-DE') ||
    voices.find(v => v.lang.startsWith('de')) ||
    null
  );
};

export const speakGerman = (text, onEnd = null, rate = 0.85) => {
  if (!hasSpeechSynthesis()) {
    console.warn('Speech synthesis is not supported in this browser.');
    if (onEnd) onEnd();
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const cleanText = text.replace(/[*_#`[\]()]/g, '').trim();
  if (!cleanText) {
    if (onEnd) onEnd();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = 'de-DE';
  utterance.rate = Math.max(0.5, Math.min(1.5, rate));

  const voice = getGermanVoice();
  if (voice) {
    utterance.voice = voice;
  }

  utterance.onend = () => {
    if (onEnd) onEnd();
  };

  utterance.onerror = (e) => {
    console.warn('Speech synthesis error:', e);
    if (onEnd) onEnd();
  };

  window.speechSynthesis.speak(utterance);
};

export const stopSpeech = () => {
  if (hasSpeechSynthesis()) {
    window.speechSynthesis.cancel();
  }
};

export const hasSpeechRecognition = () => {
  if (typeof window === 'undefined') return false;
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
};

export const createSpeechRecognizer = ({
  lang = 'de-DE',
  onResult,
  onError,
  onEnd
}) => {
  if (!hasSpeechRecognition()) {
    return null;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.lang = lang;
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    if (event.results && event.results.length > 0) {
      const transcript = event.results[0][0].transcript;
      if (onResult) onResult(transcript);
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition event error:', event.error);
    if (onError) onError(event.error);
  };

  recognition.onend = () => {
    if (onEnd) onEnd();
  };

  return recognition;
};
