# -*- coding: utf-8 -*-
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import build
from check import verify


class BlogBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        shutil.copy(build.ROOT/'site.json',self.root/'site.json')
        for name in ('content','public'):
            shutil.copytree(build.ROOT/name,self.root/name)

    def tearDown(self):
        self.temp.cleanup()

    def metadata(self,source_slug='agent-context-state',**changes):
        path=self.root/'content/articles'/(source_slug+'.html')
        raw=path.read_text()
        pattern=r'(<script type="application/json" id="article-meta">)(.*?)(</script>)'
        match=re.search(pattern,raw,re.S)
        meta=json.loads(match.group(2));meta.update(changes)
        encoded=json.dumps(meta,ensure_ascii=False).replace('<','\\u003c')
        path.write_text(raw[:match.start(2)]+encoded+raw[match.end(2):])
        return path

    def test_complete_build_and_source_isolation(self):
        source=self.root/'content/articles/agent-context-state.html'
        original=source.read_bytes()
        result=build.build(self.root)
        self.assertEqual(result['articles'],4)
        self.assertEqual(source.read_bytes(),original)
        self.assertEqual((self.root/'dist/standalone/agent-context-state.html').read_bytes(),original)
        rendered=(self.root/'dist/articles/agent-context-state/index.html').read_text()
        source_main=re.search(r'<main\b[^>]*>(.*?)</main>',original.decode(),re.S).group(1)
        output_main=re.search(r'<main\b[^>]*>(.*?)</main>',rendered,re.S).group(1)
        self.assertEqual(source_main,output_main)
        self.assertEqual(verify(self.root/'dist')[1],4)

    def test_drafts_are_absent_from_all_public_outputs(self):
        self.metadata(draft=True)
        build.build(self.root)
        dist=self.root/'dist'
        self.assertFalse((dist/'articles/agent-context-state').exists())
        self.assertFalse((dist/'standalone/agent-context-state.html').exists())
        index=json.loads((dist/'search-index.json').read_text())
        self.assertEqual(len(index['articles']),3)
        self.assertNotIn('/articles/agent-context-state/',(dist/'index.html').read_text())
        self.assertNotIn('/articles/agent-context-state/',(dist/'topics/context-management/index.html').read_text())

    def test_rebuild_removes_old_article_and_download(self):
        build.build(self.root)
        (self.root/'content/articles/agent-context-state.html').unlink()
        build.build(self.root)
        self.assertFalse((self.root/'dist/articles/agent-context-state').exists())
        self.assertFalse((self.root/'dist/standalone/agent-context-state.html').exists())
        self.assertEqual(verify(self.root/'dist')[1],3)

    def test_project_path_links_search_and_feeds(self):
        build.build(self.root,base_path='/my-blog',site_url='https://example.github.io/my-blog')
        verify(self.root/'dist','/my-blog')
        index=json.loads((self.root/'dist/search-index.json').read_text())
        self.assertTrue(all(a['url'].startswith('/my-blog/articles/') for a in index['articles']))
        rss=ET.parse(self.root/'dist/feed.xml').getroot()
        self.assertEqual(len(rss.findall('./channel/item')),4)
        self.assertTrue(all(item.text.startswith('https://example.github.io/my-blog/') for item in rss.findall('./channel/item/link')))
        sitemap=ET.parse(self.root/'dist/sitemap.xml').getroot()
        urls=[el.text for el in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertTrue(any('%' in url for url in urls))
        self.assertTrue(all(url.startswith('https://example.github.io/my-blog/') for url in urls))

    def test_mixed_case_repository_path_is_preserved(self):
        build.build(self.root,base_path='/wWzZb',site_url='https://wwzzb.github.io/wWzZb')
        dist=self.root/'dist'
        self.assertEqual(verify(dist,'/wWzZb')[1],4)
        self.assertIn('href="/wWzZb/assets/site.css"',(dist/'index.html').read_text())
        index=json.loads((dist/'search-index.json').read_text())
        self.assertTrue(all(a['url'].startswith('/wWzZb/articles/') for a in index['articles']))
        rss=ET.parse(dist/'feed.xml').getroot()
        self.assertTrue(all(item.text.startswith('https://wwzzb.github.io/wWzZb/') for item in rss.findall('./channel/item/link')))
        for path in ('/wWzZb/../secret','/wWzZb?q=1','/wWzZb/#hash'):
            with self.assertRaises(build.BuildError):build.normalize_base(path)

    def test_custom_domain_root_and_metadata_escaping(self):
        self.metadata(description='A & B <script>alert("x")</script>')
        build.build(self.root,base_path='',site_url='https://blog.example.com')
        verify(self.root/'dist')
        home=(self.root/'dist/index.html').read_text()
        self.assertIn('&lt;script&gt;',home)
        self.assertNotIn('<script>alert',home)
        ET.parse(self.root/'dist/feed.xml')
        index=json.loads((self.root/'dist/search-index.json').read_text())
        self.assertTrue(any('<script>' in a['description'] for a in index['articles']))

    def test_failed_validation_preserves_previous_build(self):
        build.build(self.root)
        previous=(self.root/'dist/index.html').read_bytes()
        self.metadata(date='2026-02-30')
        with self.assertRaises(build.BuildError):build.build(self.root)
        self.assertEqual(previous,(self.root/'dist/index.html').read_bytes())

    def test_path_traversal_slug_and_tag_rejected(self):
        self.metadata(slug='../../escape')
        with self.assertRaises(build.BuildError):build.build(self.root)
        self.metadata(slug='agent-context-state',tags=['..'])
        with self.assertRaises(build.BuildError):build.build(self.root)

    def test_unknown_category_and_topic_rejected(self):
        self.metadata(category='typo')
        with self.assertRaises(build.BuildError):build.build(self.root)
        self.metadata(category='agent-engineering',topics={'unknown':1})
        with self.assertRaises(build.BuildError):build.build(self.root)

    def test_duplicate_slugs_and_topic_order_rejected(self):
        other=self.root/'content/articles/duplicate.html'
        shutil.copy(self.root/'content/articles/agent-context-state.html',other)
        with self.assertRaises(build.BuildError):build.build(self.root)
        other.unlink()
        self.metadata(topics={'context-management':2})
        with self.assertRaises(build.BuildError):build.build(self.root)

    def test_local_preview_omits_fake_production_urls(self):
        build.build(self.root)
        self.assertFalse((self.root/'dist/sitemap.xml').exists())
        self.assertFalse((self.root/'dist/feed.xml').exists())
        self.assertIn('Disallow: /',(self.root/'dist/robots.txt').read_text())
        self.assertNotIn('rel="canonical"',(self.root/'dist/index.html').read_text())

    def test_plain_text_index_ignores_metadata_and_styles(self):
        build.build(self.root)
        index=json.loads((self.root/'dist/search-index.json').read_text())
        for article in index['articles']:
            self.assertNotIn('--paper:',article['text'])
            self.assertNotIn('"draft":',article['text'])
            self.assertNotIn('blog-site-nav',article['text'])
            self.assertTrue(article['headings'])
        self.assertTrue(any('6144' in a['text'] for a in index['articles']))

    def test_source_requires_explicit_draft_and_independent_assets(self):
        self.metadata(draft='false')
        with self.assertRaises(build.BuildError):build.build(self.root)
        path=self.metadata(draft=False)
        path.write_text(path.read_text().replace('</main>','<img src="local.png"></main>'))
        with self.assertRaises(build.BuildError):build.build(self.root)

    def test_site_url_path_must_match_deployment_prefix(self):
        with self.assertRaises(build.BuildError):
            build.build(self.root,base_path='/blog',site_url='https://example.com')

    def test_draft_only_site_builds_without_dead_topic_links(self):
        for path in (self.root/'content/articles').glob('*.html'):
            self.metadata(path.stem,draft=True)
        result=build.build(self.root)
        self.assertEqual(result['articles'],0)
        self.assertEqual(verify(self.root/'dist')[1],0)

    def test_new_article_command_creates_safe_draft_and_never_overwrites(self):
        for filename in ('new_article.py','build.py'):
            shutil.copy(build.ROOT/filename,self.root/filename)
        shutil.copytree(build.ROOT/'templates',self.root/'templates')
        command=[sys.executable,'-B',str(self.root/'new_article.py'),'new-topic','--title','标题 <示例> {{META}}']
        first=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(first.returncode,0,first.stderr)
        target=self.root/'content/articles/new-topic.html'
        content=target.read_bytes()
        article=build.parse_article(target,build.load_config(self.root))
        self.assertEqual(article.title,'标题 <示例> {{META}}')
        self.assertTrue(article.meta['draft'])
        self.assertEqual(build.build(self.root)['articles'],4)
        second=subprocess.run(command,capture_output=True,text=True)
        self.assertNotEqual(second.returncode,0)
        self.assertEqual(content,target.read_bytes())


if __name__=='__main__':unittest.main()
