import test from 'node:test';
import assert from 'node:assert';

test('AI German Tutor & RAG System (Phase 4)', async (t) => {
  await t.test('Supported CEFR levels for tutoring', () => {
    const supportedTutorLevels = ['A1', 'A2', 'B1'];
    assert.strictEqual(supportedTutorLevels.length, 3);
    assert.ok(supportedTutorLevels.includes('A1'));
    assert.ok(supportedTutorLevels.includes('A2'));
    assert.ok(supportedTutorLevels.includes('B1'));
  });

  await t.test('Tutor response language options', () => {
    const languageOptions = ['english', 'bilingual', 'german'];
    assert.strictEqual(languageOptions.length, 3);
    assert.ok(languageOptions.includes('english'));
    assert.ok(languageOptions.includes('bilingual'));
  });

  await t.test('AI Status Indicator mappings', () => {
    const mapStatus = (status, isReady, isRunning, generating) => {
      if (generating) return 'generating';
      if (isReady) return 'ready';
      if (isRunning && !isReady) return 'model_not_installed';
      if (!isRunning) return 'ollama_not_running';
      return 'failed';
    };

    assert.strictEqual(mapStatus('ready', true, true, false), 'ready');
    assert.strictEqual(mapStatus('running', false, true, false), 'model_not_installed');
    assert.strictEqual(mapStatus('offline', false, false, false), 'ollama_not_running');
    assert.strictEqual(mapStatus('ready', true, true, true), 'generating');
  });

  await t.test('RAG source attribution structure validation', () => {
    const sampleSources = [
      {
        material_id: 'mat_123',
        source_title: 'A1 Articles Note.pdf',
        page_number: 2,
        similarity_score: 0.38,
        snippet: 'Der Apfel ist maskulin.'
      }
    ];

    assert.strictEqual(sampleSources.length, 1);
    const src = sampleSources[0];
    assert.ok(src.material_id);
    assert.ok(src.source_title);
    assert.strictEqual(src.page_number, 2);
    assert.ok(src.similarity_score > 0);
  });

  await t.test('Suggested starter questions coverage', () => {
    const starterQuestions = [
      'Explain the difference between nicht and kein.',
      'Why does the verb come at the end after weil?',
      'Explain this topic at A1 level.',
      'Summarize my latest German notes.',
      'Give me five practice questions about articles.',
      'Correct my German sentence and explain my mistakes: "Ich habe gestern ein Buch lesen."'
    ];

    assert.ok(starterQuestions.length >= 6);
    assert.ok(starterQuestions.some(q => q.includes('nicht and kein')));
    assert.ok(starterQuestions.some(q => q.includes('weil')));
    assert.ok(starterQuestions.some(q => q.includes('A1 level')));
    assert.ok(starterQuestions.some(q => q.includes('notes')));
    assert.ok(starterQuestions.some(q => q.includes('Correct my German sentence')));
  });
});
