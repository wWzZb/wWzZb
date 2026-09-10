const test = require('node:test');
const assert = require('node:assert/strict');
const {search, terms, snippet} = require('../public/assets/search.js');
const make = (title, text, extra = {}) => ({title, text, description: '', tags: [], headings: [], category: 'agent', date: '2026-09-09', ...extra});

test('Chinese full-text matching finds body-only facts', () => {
  const articles = [make('预算机制', '提醒阈值为 6144 token'), make('其他', '无关内容')];
  assert.equal(search(articles, '6144')[0].article.title, '预算机制');
  assert.equal(search(articles, '提醒阈值').length, 1);
});
test('Multiple keywords use AND and category filter is applied', () => {
  const articles = [make('上下文', '笔记交接'), make('上下文', '代码修改'), make('上下文', '笔记交接', {category: 'other'})];
  assert.equal(search(articles, '上下文 笔记', 'agent').length, 1);
});
test('Titles rank before body-only occurrences', () => {
  const articles = [make('一般记录', '外部记忆'), make('外部记忆', '说明')];
  assert.equal(search(articles, '外部记忆')[0].article.title, '外部记忆');
});
test('Case and full-width Latin characters are normalized', () => {
  assert.equal(search([make('Agent Runtime', 'token')], 'ＡＧＥＮＴ').length, 1);
  assert.deepEqual(terms('  Token token  笔记 '), ['token', '笔记']);
});
test('Empty queries and literal special characters are harmless', () => {
  const articles = [make('x', 'a+b [tag] <script>')];
  assert.equal(search(articles, '   ').length, 0);
  assert.equal(search(articles, 'a+b').length, 1);
  assert.equal(search(articles, '[tag]').length, 1);
  assert.equal(search(articles, '不存在').length, 0);
});
test('Snippet brings a late body match into view', () => {
  const text = '前文'.repeat(120) + '目标关键词' + '后文'.repeat(120);
  const result = snippet(text, '目标关键词');
  assert.ok(result.includes('目标关键词'));
  assert.ok(result.startsWith('…'));
  assert.ok(result.length <= 162);
});
