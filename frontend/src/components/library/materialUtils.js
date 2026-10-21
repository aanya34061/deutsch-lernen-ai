export const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png'];
export const SUPPORTED_CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
export const SUPPORTED_TOPICS = ['Grammar', 'Vocabulary', 'Lesen', 'Hören', 'Schreiben', 'Sprechen', 'General'];
export const SUPPORTED_STATUSES = ['uploaded', 'processing', 'ready', 'failed'];

export const getTypeLabel = (fileType = '') => {
  const map = {
    pdf: 'PDF',
    docx: 'DOCX',
    txt: 'TXT',
    image: 'IMAGE',
    youtube: 'YOUTUBE',
    link: 'LINK',
    audio: 'AUDIO',
  };
  return map[fileType.toLowerCase()] || fileType.toUpperCase();
};

export const formatFileSize = (bytes) => {
  if (!bytes || bytes <= 0) return null;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

export const formatDate = (isoString) => {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return isoString;
  }
};
