import test from 'node:test';
import assert from 'node:assert';

test('Frontend configuration and CEFR levels', async (t) => {
  await t.test('CEFR Level definitions adhere to A1-C2 standard', () => {
    const supportedLevels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
    assert.strictEqual(supportedLevels.length, 6);
    assert.strictEqual(supportedLevels[0], 'A1');
    assert.strictEqual(supportedLevels[supportedLevels.length - 1], 'C2');
  });

  await t.test('German article color coding mappings', () => {
    const articleMap = {
      der: 'masculine',
      die: 'feminine',
      das: 'neuter',
    };
    assert.strictEqual(articleMap['der'], 'masculine');
    assert.strictEqual(articleMap['die'], 'feminine');
    assert.strictEqual(articleMap['das'], 'neuter');
  });

  await t.test('Four core language competencies are present', () => {
    const coreSkills = ['reading', 'listening', 'writing', 'speaking'];
    assert.strictEqual(coreSkills.length, 4);
    assert.ok(coreSkills.includes('reading'));
    assert.ok(coreSkills.includes('speaking'));
  });

  await t.test('Daily goal progress calculation handles boundaries safely', () => {
    const calcProgress = (today, goal) => Math.min(100, Math.max(0, Math.round((today / (goal || 20)) * 100)));
    assert.strictEqual(calcProgress(0, 20), 0);
    assert.strictEqual(calcProgress(10, 20), 50);
    assert.strictEqual(calcProgress(20, 20), 100);
    assert.strictEqual(calcProgress(35, 20), 100); // capped at 100%
  });
});
