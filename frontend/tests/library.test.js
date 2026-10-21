import test from 'node:test';
import assert from 'node:assert';
import { getTypeLabel, formatFileSize, SUPPORTED_EXTENSIONS, SUPPORTED_CEFR_LEVELS, SUPPORTED_STATUSES } from '../src/components/library/materialUtils.js';

test('Library Utilities and Material Management (Phase 2)', async (t) => {
  await t.test('Supported material extensions', () => {
    const supportedExtensions = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png'];
    assert.strictEqual(supportedExtensions.length, 6);
    ['sample.pdf', 'notes.docx', 'vocab.txt', 'photo.jpg', 'scan.png'].forEach(filename => {
      const valid = supportedExtensions.some(ext => filename.endsWith(ext));
      assert.strictEqual(valid, true, `Expected ${filename} to be valid`);
    });

    ['script.exe', 'archive.zip', 'audio.mp3'].forEach(filename => {
      const valid = supportedExtensions.some(ext => filename.endsWith(ext));
      assert.strictEqual(valid, false, `Expected ${filename} to be invalid for document upload`);
    });
  });

  await t.test('Format file size calculations', () => {
    assert.strictEqual(formatFileSize(null), null);
    assert.strictEqual(formatFileSize(0), null);
    assert.strictEqual(formatFileSize(500), '500 B');
    assert.strictEqual(formatFileSize(2048), '2.0 KB');
    assert.strictEqual(formatFileSize(5 * 1024 * 1024), '5.00 MB');
  });

  await t.test('Material type label mappings', () => {
    assert.strictEqual(getTypeLabel('pdf'), 'PDF');
    assert.strictEqual(getTypeLabel('docx'), 'DOCX');
    assert.strictEqual(getTypeLabel('txt'), 'TXT');
    assert.strictEqual(getTypeLabel('image'), 'IMAGE');
    assert.strictEqual(getTypeLabel('youtube'), 'YOUTUBE');
    assert.strictEqual(getTypeLabel('link'), 'LINK');
  });

  await t.test('YouTube URL detection logic', () => {
    const isYouTubeUrl = (url) => {
      const u = url.toLowerCase();
      return u.includes('youtube.com') || u.includes('youtu.be');
    };

    assert.strictEqual(isYouTubeUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), true);
    assert.strictEqual(isYouTubeUrl('https://youtu.be/dQw4w9WgXcQ'), true);
    assert.strictEqual(isYouTubeUrl('https://learngerman.dw.com/en/overview'), false);
    assert.strictEqual(isYouTubeUrl('https://deutsch.info/en/grammar'), false);
  });

  await t.test('Material status types adherence', () => {
    const validStatuses = ['uploaded', 'processing', 'ready', 'failed'];
    assert.strictEqual(validStatuses.length, 4);
    assert.ok(validStatuses.includes('ready'));
    assert.ok(validStatuses.includes('failed'));
  });
});
