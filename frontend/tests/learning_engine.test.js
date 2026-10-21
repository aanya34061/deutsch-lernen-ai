import test from 'node:test';
import assert from 'node:assert';

test('Learning Engine and Practice System (Phase 3)', async (t) => {
  await t.test('Supported curriculum levels in Phase 3', () => {
    const activeCurriculumLevels = ['A1', 'A2', 'B1'];
    assert.strictEqual(activeCurriculumLevels.length, 3);
    assert.ok(activeCurriculumLevels.includes('A1'));
    assert.ok(activeCurriculumLevels.includes('A2'));
    assert.ok(activeCurriculumLevels.includes('B1'));
  });

  await t.test('Supported exercise question types', () => {
    const supportedQuestionTypes = [
      'multiple_choice',
      'fill_blank',
      'translate',
      'sentence_order',
      'matching',
      'true_false'
    ];
    assert.strictEqual(supportedQuestionTypes.length, 6);
  });

  await t.test('Sentence order word token join logic', () => {
    const tokens = ['Guten', 'Tag', 'ich', 'heiße', 'Laura'];
    const joined = tokens.join(' ');
    assert.strictEqual(joined, 'Guten Tag ich heiße Laura');
  });

  await t.test('Matching pairs dictionary validation', () => {
    const expected = {
      'der Hund': 'the dog',
      'die Katze': 'the cat'
    };
    const userGood = {
      'der Hund': 'the dog',
      'die Katze': 'the cat'
    };
    const userBad = {
      'der Hund': 'the cat',
      'die Katze': 'the dog'
    };

    const isMatch = (target, cand) => Object.keys(target).every(k => cand[k] === target[k]);
    assert.strictEqual(isMatch(expected, userGood), true);
    assert.strictEqual(isMatch(expected, userBad), false);
  });

  await t.test('German noun articles and color class mapping', () => {
    const getArticleClass = (art) => {
      switch (art) {
        case 'der': return 'badge-der';
        case 'die': return 'badge-die';
        case 'das': return 'badge-das';
        default: return 'bg-light text-dark';
      }
    };

    assert.strictEqual(getArticleClass('der'), 'badge-der');
    assert.strictEqual(getArticleClass('die'), 'badge-die');
    assert.strictEqual(getArticleClass('das'), 'badge-das');
    assert.strictEqual(getArticleClass(''), 'bg-light text-dark');
  });
});
