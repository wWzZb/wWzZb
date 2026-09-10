#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small HTML-first blog builder. Python 3.9+, standard library only."""
import argparse
import copy
import datetime as dt
import html
import json
import math
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class BuildError(ValueError):
    pass


def escaped(value):
    return html.escape(str(value), quote=True)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def plain(parts):
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metadata = []
        self.meta_active = False
        self.main_depth = 0
        self.ignore_depth = 0
        self.h1_depth = 0
        self.main_count = 0
        self.h1_count = 0
        self.title = []
        self.text = []
        self.ids = []
        self.headings = []
        self.heading = None
        self.has_charset = False
        self.has_viewport = False
        self.has_canonical = False
        self.local_references = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            value = attrs.get(key, "")
            if value and not value.startswith(("#", "data:", "https://", "http://", "mailto:", "tel:")):
                self.local_references.append(value)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "meta":
            self.has_charset |= attrs.get("charset", "").lower() == "utf-8"
            self.has_viewport |= attrs.get("name") == "viewport"
        if tag == "link" and attrs.get("rel") == "canonical":
            self.has_canonical = True
        if tag == "script" and attrs.get("id") == "article-meta":
            if attrs.get("type") != "application/json":
                raise BuildError("article-meta 必须使用 application/json")
            self.metadata.append("")
            self.meta_active = True
        if tag in ("style", "script", "template"):
            self.ignore_depth += 1
        if tag == "main":
            self.main_depth += 1
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1
            self.h1_depth += 1
        if self.main_depth and tag in ("h2", "h3"):
            self.heading = []

    def handle_endtag(self, tag):
        if tag == "script":
            self.meta_active = False
        if tag in ("style", "script", "template"):
            self.ignore_depth = max(0, self.ignore_depth - 1)
        if tag == "main":
            self.main_depth = max(0, self.main_depth - 1)
        if tag == "h1":
            self.h1_depth = max(0, self.h1_depth - 1)
        if tag in ("h2", "h3") and self.heading is not None:
            self.headings.append(plain(self.heading))
            self.heading = None

    def handle_data(self, data):
        if self.meta_active:
            self.metadata[-1] += data
        if self.ignore_depth:
            return
        if self.h1_depth:
            self.title.append(data)
        if self.main_depth:
            self.text.append(data)
            if self.heading is not None:
                self.heading.append(data)


@dataclass
class Article:
    source: Path
    raw: str
    meta: dict
    title: str
    text: str
    headings: list
    minutes: int

    @property
    def slug(self):
        return self.meta["slug"]

    @property
    def path(self):
        return "articles/" + self.slug + "/"


def require_slug(value, name):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise BuildError(f"{name} 必须是小写英文、数字和连字符组成的标识")


def require_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{name} 必须是非空文本")


def normalize_base(value):
    if value in ("", "/"):
        return ""
    if not isinstance(value, str) or not value.startswith("/"):
        raise BuildError("base_path 必须为空或以 / 开头，例如 /personal-blog")
    parts = value.strip("/").split("/")
    # GitHub repository paths are case-sensitive; validate without changing them.
    if any(not SLUG.fullmatch(part.lower()) for part in parts):
        raise BuildError("base_path 只能包含英文字母、数字和连字符路径段，不得包含 ..、空格或查询参数")
    return "/" + "/".join(parts)


def normalize_site_url(value):
    if not value:
        return ""
    parsed = urlsplit(value)
    if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise BuildError("site_url 必须是完整的网站地址，不含认证、查询参数或片段")
    if any(p in (".", "..") for p in parsed.path.split("/")):
        raise BuildError("site_url 路径无效")
    return value.rstrip("/")


def load_config(root, base_path=None, site_url=None):
    try:
        config = json.loads((root / "site.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"无法读取 site.json：{exc}") from exc
    if not isinstance(config, dict):
        raise BuildError("site.json 必须是 JSON 对象")
    for name in ("title", "description", "language"):
        require_text(config.get(name), "site." + name)
    for name in ("categories", "topics"):
        if not isinstance(config.get(name), dict):
            raise BuildError(f"site.{name} 必须是对象")
        for slug, item in config[name].items():
            require_slug(slug, name)
            if not isinstance(item, dict):
                raise BuildError(f"{name}.{slug} 必须是对象")
            require_text(item.get("name"), name + ".name")
            require_text(item.get("description"), name + ".description")
    config = copy.deepcopy(config)
    config["base_path"] = normalize_base(config.get("base_path", "") if base_path is None else base_path)
    config["site_url"] = normalize_site_url(config.get("site_url", "") if site_url is None else site_url)
    if config["site_url"]:
        configured_path = urlsplit(config["site_url"]).path.rstrip("/")
        if configured_path != config["base_path"]:
            raise BuildError("site_url 的路径必须与 base_path 一致；自定义域名通常使用空 base_path")
    return config


def parse_article(path, config):
    if path.is_symlink():
        raise BuildError(f"禁止把符号链接当成文章：{path.name}")
    raw = path.read_text(encoding="utf-8")
    parser = ArticleParser()
    parser.feed(raw)
    if len(parser.metadata) != 1:
        raise BuildError(f"{path.name} 必须包含且只包含一个 article-meta JSON 块")
    try:
        meta = json.loads(parser.metadata[0])
    except json.JSONDecodeError as exc:
        raise BuildError(f"{path.name} 的元数据 JSON 无效：{exc}") from exc
    if not isinstance(meta, dict):
        raise BuildError(f"{path.name} 的元数据必须是对象")
    require_slug(meta.get("slug"), "slug")
    require_text(meta.get("description"), "description")
    if type(meta.get("draft")) is not bool:
        raise BuildError(f"{path.name} 的 draft 必须显式填写 true 或 false")
    for field in ("date", "updated"):
        if field == "updated" and field not in meta:
            continue
        value = meta.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise BuildError(f"{path.name} 的 {field} 必须为 YYYY-MM-DD")
        try:
            dt.date.fromisoformat(value)
        except ValueError as exc:
            raise BuildError(f"{path.name} 的日期无效：{value}") from exc
    if meta.get("updated", meta["date"]) < meta["date"]:
        raise BuildError("updated 不得早于 date")
    if meta.get("category") not in config["categories"]:
        raise BuildError(f"{path.name} 引用了未定义的分类")
    tags = meta.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() or tag in (".", "..") or tag != tag.strip() or '%' in tag or any(ch in tag for ch in '/\\#?') or any(ord(ch) < 32 for ch in tag) for tag in tags):
        raise BuildError(f"{path.name} 的 tags 必须是合法标签数组")
    if len(tags) != len(set(tags)):
        raise BuildError(f"{path.name} 有重复标签")
    topics = meta.get("topics", {})
    if not isinstance(topics, dict):
        raise BuildError("topics 必须是 专题标识: 阅读顺序 的对象")
    for topic, order in topics.items():
        if topic not in config["topics"] or type(order) is not int or order < 1:
            raise BuildError(f"{path.name} 的专题或阅读顺序无效")
    if not raw.lstrip().lower().startswith("<!doctype html>") or not re.search(r"</head\s*>", raw, re.I) or not re.search(r"</body\s*>", raw, re.I):
        raise BuildError(f"{path.name} 必须是完整 HTML 文档")
    if not parser.has_charset or not parser.has_viewport or parser.main_count != 1 or parser.h1_count != 1:
        raise BuildError(f"{path.name} 需要 UTF-8、viewport、一个 main 和一个 h1")
    if parser.has_canonical:
        raise BuildError(f"{path.name} 请去掉手写 canonical，由构建器按部署地址生成")
    if parser.local_references:
        raise BuildError(f"{path.name} 引用了相对或本机资源 {parser.local_references[0]!r}；独立文章应内联资源或使用完整 HTTPS 地址")
    if len(parser.ids) != len(set(parser.ids)):
        raise BuildError(f"{path.name} 包含重复的 HTML id")
    title, text = plain(parser.title), plain(parser.text)
    require_text(title, "h1")
    require_text(text, "main 正文")
    # Chinese characters and Latin words are both counted, rather than code bytes.
    units = len(re.findall(r"[\u3400-\u9fff]|[a-zA-Z0-9_]+", text))
    return Article(path, raw, meta, title, text, parser.headings, max(1, math.ceil(units / 450)))


def load_articles(root, config):
    all_articles = [parse_article(path, config) for path in sorted((root / "content/articles").rglob("*.html"))]
    seen = set()
    for article in all_articles:
        if article.slug in seen:
            raise BuildError(f"重复 slug：{article.slug}")
        seen.add(article.slug)
    articles = [a for a in all_articles if not a.meta["draft"]]
    for topic in config["topics"]:
        orders = [a.meta["topics"][topic] for a in articles if topic in a.meta.get("topics", {})]
        if len(orders) != len(set(orders)):
            raise BuildError(f"专题 {topic} 的阅读顺序重复")
    return sorted(articles, key=lambda a: (a.meta["date"], a.slug), reverse=True)


class Renderer:
    def __init__(self, config, articles):
        self.config, self.articles = config, articles
        self.routes = []

    def url(self, path=""):
        return self.config["base_path"] + "/" + path.lstrip("/")

    def absolute(self, path=""):
        return self.config["site_url"] + "/" + path.lstrip("/")

    def category_name(self, article):
        return self.config["categories"][article.meta["category"]]["name"]

    def tags(self, article):
        return "".join(f'<a class="tag" href="{escaped(self.url("tags/"+quote(t,safe="")+"/"))}">{escaped(t)}</a>' for t in article.meta.get("tags", []))

    def card(self, article, index=None):
        number = f'<span class="list-number">{index:02}</span>' if index is not None else ""
        return f'''<article class="post-row">{number}<div class="post-copy"><p class="post-meta"><a href="{self.url('categories/'+article.meta['category']+'/')}">{escaped(self.category_name(article))}</a><span>·</span><time datetime="{article.meta['date']}">{article.meta['date'].replace('-', '.')}</time><span>·</span>{article.minutes} 分钟</p><h2><a href="{self.url(article.path)}">{escaped(article.title)}</a></h2><p class="post-summary">{escaped(article.meta['description'])}</p><div class="tags">{self.tags(article)}</div></div><a class="post-arrow" href="{self.url(article.path)}" aria-label="阅读：{escaped(article.title)}">↗</a></article>'''

    def list_posts(self, articles):
        return '<div class="post-list">'+"".join(self.card(a,i) for i,a in enumerate(articles,1))+'</div>' if articles else '<p class="empty">这个分类暂时还没有文章。</p>'

    def header(self, active):
        links = [("articles/", "文章", "articles"), ("categories/", "分类", "categories"), ("topics/", "专题", "topics"), ("search/", "搜索", "search")]
        nav = "".join(f'<a href="{self.url(path)}"'+(' aria-current="page"' if key==active else '')+f'>{label}</a>' for path,label,key in links)
        return f'<header class="site-header"><div class="header-inner"><a class="brand" href="{self.url()}"><span class="brand-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 5h6a3 3 0 0 1 3 3v12a4 4 0 0 0-4-2H4V5Zm16 0h-4a3 3 0 0 0-3 3m0 12a4 4 0 0 1 4-2h3V5Z"/></svg></span>{escaped(self.config["title"])}</a><nav aria-label="主导航">{nav}</nav></div></header>'

    def page(self, title, body, path, active="", description=None, search=False, noindex=False):
        description = description or self.config["description"]
        canonical = ''
        feeds = ''
        if self.config["site_url"]:
            canonical=f'<link rel="canonical" href="{escaped(self.absolute(path))}"><meta property="og:url" content="{escaped(self.absolute(path))}">'
            feeds=f'<link rel="alternate" type="application/rss+xml" title="{escaped(self.config["title"])}" href="{self.url("feed.xml")}">'
        script=f'<script src="{self.url("assets/search.js")}" defer></script>' if search else ''
        footer_feed=f'<a href="{self.url("feed.xml")}">RSS</a>' if self.config["site_url"] else ''
        return f'''<!doctype html><html lang="{escaped(self.config['language'])}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escaped(title)} · {escaped(self.config['title'])}</title><meta name="description" content="{escaped(description)}"><meta property="og:title" content="{escaped(title)}"><meta property="og:description" content="{escaped(description)}"><meta property="og:type" content="website">{canonical}{feeds}{'<meta name="robots" content="noindex">' if noindex else ''}<link rel="icon" href="{self.url('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{self.url('assets/design-tokens.css')}"><link rel="stylesheet" href="{self.url('assets/site.css')}">{script}</head><body><a class="skip" href="#main">跳到正文</a>{self.header(active)}<main id="main" class="container">{body}</main><footer class="site-footer"><div><a class="footer-brand" href="{self.url()}">{escaped(self.config['title'])}</a><p>{escaped(self.config['description'])}</p></div><div class="footer-links"><a href="{self.url('about/')}">关于</a><a href="{self.url('articles/')}">全部文章</a>{footer_feed}</div></footer></body></html>'''

    def heading(self, kicker, title, description):
        return f'<header class="page-heading"><p class="eyebrow">{escaped(kicker)}</p><h1>{escaped(title)}</h1><p>{escaped(description)}</p></header>'

    def home(self):
        categories=len({a.meta['category'] for a in self.articles})
        topic_count=len({topic for a in self.articles for topic in a.meta.get('topics',{})})
        hero=f'''<section class="hero"><div class="hero-copy"><h1>技术文章</h1><p class="hero-description">{escaped(self.config['description'])}</p><p class="hero-counts">{len(self.articles)} 篇文章 <span>·</span> {categories} 个分类 <span>·</span> {topic_count} 个专题</p></div><form class="home-search" action="{self.url('search/')}" method="get" role="search"><label for="home-query">搜索文章</label><div class="search-box"><input id="home-query" type="search" name="q" placeholder="输入标题、关键词或正文内容" maxlength="200"><button type="submit">搜索</button></div></form></section>'''
        topics=[]
        for key,topic in self.config["topics"].items():
            count=sum(key in a.meta.get("topics",{}) for a in self.articles)
            if count:
                topics.append(f'<a class="topic-mini" href="{self.url("topics/"+key+"/")}"><span class="eyebrow">专题 · {count} 篇</span><h3>{escaped(topic["name"])}</h3><p>{escaped(topic["description"])}</p><span class="text-link">查看专题 ↗</span></a>')
        category_links=''.join(f'<a class="sidebar-category" href="{self.url("categories/"+key+"/")}">{escaped(value["name"])}<span>{sum(a.meta["category"]==key for a in self.articles)}</span></a>' for key,value in self.config['categories'].items() if any(a.meta['category']==key for a in self.articles))
        latest=f'<section class="home-content"><div class="latest"><div class="section-heading"><h2>最新文章</h2><a href="{self.url("articles/")}">全部文章 <span>↗</span></a></div>{self.list_posts(self.articles[:8])}</div><aside class="home-aside"><p class="aside-title">专题</p>'+''.join(topics)+f'<div class="about-mini"><p class="aside-title">分类</p>{category_links}</div></aside></section>'
        return self.page('首页',hero+latest,'')

    def article(self, article):
        # Original HTML remains fully independent in standalone/. The published page
        # gets only scoped navigation and SEO metadata; main is never rewritten.
        canonical=''
        if self.config["site_url"]:
            canonical=f'<link rel="canonical" href="{escaped(self.absolute(article.path))}"><meta property="og:url" content="{escaped(self.absolute(article.path))}">'
        extra=f'''{canonical}<meta property="og:type" content="article"><meta property="og:title" content="{escaped(article.title)}"><meta property="og:description" content="{escaped(article.meta['description'])}"><meta property="article:published_time" content="{article.meta['date']}"><link rel="icon" href="{self.url('assets/favicon.svg')}" type="image/svg+xml"><style>.blog-site-nav{{max-width:1184px;width:calc(100% - 48px);margin:0 auto;padding:20px 0;display:flex;align-items:center;justify-content:space-between;gap:16px;font:14px/1.6 var(--font-body);border-bottom:1px solid var(--border)}}.blog-site-nav a{{color:var(--foreground);text-decoration:none;border-radius:var(--radius-full);padding:8px 16px}}.blog-site-nav>a{{font-weight:600;padding-left:0}}.blog-site-nav div{{display:flex;gap:4px;flex-wrap:wrap;align-items:center}}.blog-site-nav a:hover{{background:var(--evelab-cyan-50);color:var(--evelab-cyan-900)}}.blog-site-nav a[download]{{background:var(--primary);color:var(--foreground);padding:10px 20px}}.blog-site-nav a[download]:hover{{background:var(--evelab-cyan-600)}}@media(max-width:600px){{.blog-site-nav{{width:calc(100% - 40px);padding:16px 0;flex-wrap:wrap;font-size:12px}}.blog-site-nav div{{gap:0}}.blog-site-nav div a{{padding:8px 12px}}}}@media print{{.blog-site-nav{{display:none}}}}</style>'''
        raw = re.sub(r'</head\s*>',lambda _:extra+'</head>',article.raw,count=1,flags=re.I)
        nav=f'<nav class="blog-site-nav" aria-label="博客导航"><a href="{self.url()}">← {escaped(self.config["title"])}</a><div><a href="{self.url("categories/"+article.meta["category"]+"/")}">{escaped(self.category_name(article))}</a><a href="{self.url("search/")}">搜索</a><a href="{self.url("standalone/"+article.slug+".html")}" download>下载 HTML</a></div></nav>'
        return re.sub(r'(<body\b[^>]*>)',lambda m:m.group(1)+nav,raw,count=1,flags=re.I)


def write(root, path, content):
    target=root/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(content,encoding="utf-8")


def build(root=ROOT, base_path=None, site_url=None):
    root=Path(root).resolve()
    config=load_config(root,base_path,site_url)
    articles=load_articles(root,config)
    renderer=Renderer(config,articles)
    staging=Path(tempfile.mkdtemp(prefix=".build-",dir=root))
    routes=[]
    today=max((a.meta.get("updated",a.meta["date"]) for a in articles),default="1970-01-01")
    def page(route,markup,lastmod=today):
        write(staging,route+"index.html",markup)
        routes.append((route,lastmod))
    try:
        public=root/"public"
        if public.exists():
            for item in public.rglob('*'):
                if item.is_symlink():raise BuildError("public 中不允许符号链接")
            shutil.copytree(public,staging,dirs_exist_ok=True)
        page('',renderer.home())
        page('articles/',renderer.page('全部文章',renderer.heading('ARTICLES','全部文章',f'共 {len(articles)} 篇文章，记录原理、实现与实践。')+renderer.list_posts(articles),'articles/','articles'))
        for article in articles:
            page(article.path,renderer.article(article),article.meta.get("updated",article.meta["date"]))
            write(staging,'standalone/'+article.slug+'.html',article.raw)
        categories=''
        for slug,category in config['categories'].items():
            group=[a for a in articles if a.meta['category']==slug]
            if not group:continue
            categories+=f'<a class="taxonomy-card" href="{renderer.url("categories/"+slug+"/")}"><span>{len(group):02} 篇文章</span><h2>{escaped(category["name"])}</h2><p>{escaped(category["description"])}</p><b aria-hidden="true">↗</b></a>'
            route='categories/'+slug+'/'
            page(route,renderer.page(category['name'],renderer.heading('CATEGORY',category['name'],category['description'])+renderer.list_posts(group),route,'categories'))
        page('categories/',renderer.page('分类',renderer.heading('CATEGORIES','按领域阅读','从一个技术领域进入，找到相关的原理与实践。')+'<div class="taxonomy-grid">'+categories+'</div>','categories/','categories'))
        topics=''
        for slug,topic in config['topics'].items():
            group=sorted((a for a in articles if slug in a.meta.get('topics',{})),key=lambda a:a.meta['topics'][slug])
            if not group:continue
            topics+=f'<a class="taxonomy-card topic-card" href="{renderer.url("topics/"+slug+"/")}"><span>阅读路径 · {len(group)} 篇</span><h2>{escaped(topic["name"])}</h2><p>{escaped(topic["description"])}</p><b aria-hidden="true">↗</b></a>'
            route='topics/'+slug+'/'
            intro=f'<div class="topic-intro"><span>阅读这组文章</span><p>{escaped(topic.get("intro",topic["description"]))}</p></div>'
            page(route,renderer.page(topic['name'],renderer.heading('TOPIC',topic['name'],topic['description'])+intro+renderer.list_posts(group),route,'topics'))
        page('topics/',renderer.page('专题',renderer.heading('TOPICS','专题','按主题组织的文章合集，包含建议阅读顺序。')+'<div class="taxonomy-grid">'+topics+'</div>','topics/','topics'))
        tags=sorted({tag for a in articles for tag in a.meta.get('tags',[])})
        for tag in tags:
            group=[a for a in articles if tag in a.meta.get('tags',[])]
            route='tags/'+quote(tag,safe='')+'/'
            # Actual filenames are decoded so static servers can resolve encoded URLs.
            decoded='tags/'+tag+'/'
            page(decoded,renderer.page(tag,renderer.heading('TAG',tag,f'{len(group)} 篇相关文章')+renderer.list_posts(group),route,'articles'))
            routes[-1]=(route,today)
        search_body=renderer.heading('SEARCH','搜索文章','搜索标题、标签和完整正文。多个关键词用空格分隔。')+f'''<form id="search-form" class="search-form" role="search"><label for="search-input">搜索关键词</label><div class="search-box"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><input id="search-input" name="q" type="search" placeholder="例如：上下文、笔记、运行时" autocomplete="off" maxlength="200"><button type="submit">搜索</button></div></form><div class="search-tools"><label for="search-category">分类</label><select id="search-category"><option value="">全部分类</option>'''+''.join(f'<option value="{slug}">{escaped(c["name"])}</option>' for slug,c in config['categories'].items())+f'''</select></div><p id="search-status" class="search-status" role="status" aria-live="polite">输入关键词开始搜索。</p><div id="search-results" class="search-results" data-index="{renderer.url('search-index.json')}"></div><noscript><p class="empty">搜索需要 JavaScript。你仍可浏览<a href="{renderer.url('articles/')}">全部文章</a>。</p></noscript>'''
        page('search/',renderer.page('搜索',search_body,'search/','search',search=True))
        author=escaped(config.get('author') or config['title'])
        about=renderer.heading('ABOUT','关于博客',config['description'])+'<div class="prose"><p>这里收录 Agent 工程相关的技术文章，包括上下文管理、外部记忆、任务恢复和运行时控制。文章包含原理说明、实现示例和参考资料。</p><h2>浏览方式</h2><p>文章列表按发布时间排列；分类按技术领域组织；专题提供一组相关文章及阅读顺序。搜索支持标题、标签和正文。</p><h2>文章下载</h2><p>每篇文章顶部提供 HTML 下载入口，可单独保存和离线阅读。参考资料中的外部链接需要联网访问。</p></div>'
        page('about/',renderer.page('关于',about,'about/'))
        write(staging,'404.html',renderer.page('页面未找到',renderer.heading('404','这页不在这里','链接可能已经变更，试试搜索或回到文章列表。')+f'<div class="error-actions"><a class="button" href="{renderer.url("articles/")}">查看文章</a><a href="{renderer.url("search/")}">搜索 →</a></div>','404.html',noindex=True))
        index=[{'title':a.title,'description':a.meta['description'],'url':renderer.url(a.path),'date':a.meta['date'],'category':a.meta['category'],'categoryName':renderer.category_name(a),'tags':a.meta.get('tags',[]),'headings':a.headings,'text':a.text,'minutes':a.minutes} for a in articles]
        write(staging,'search-index.json',json_text({'version':1,'articles':index})+'\n')
        write(staging,'.nojekyll','')
        if config['site_url']:
            namespace='http://www.sitemaps.org/schemas/sitemap/0.9'
            ET.register_namespace('',namespace)
            sitemap=ET.Element('{'+namespace+'}urlset')
            for route,lastmod in routes:
                item=ET.SubElement(sitemap,'{'+namespace+'}url')
                ET.SubElement(item,'{'+namespace+'}loc').text=renderer.absolute(route)
                ET.SubElement(item,'{'+namespace+'}lastmod').text=lastmod
            write(staging,'sitemap.xml',ET.tostring(sitemap,encoding='unicode',xml_declaration=True))
            rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel')
            for name,value in [('title',config['title']),('link',renderer.absolute()),('description',config['description']),('language',config['language'])]:ET.SubElement(channel,name).text=value
            for a in articles:
                item=ET.SubElement(channel,'item')
                for name,value in [('title',a.title),('link',renderer.absolute(a.path)),('guid',renderer.absolute(a.path)),('description',a.meta['description']),('pubDate',dt.datetime.strptime(a.meta['date'],'%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0000'))]:ET.SubElement(item,name).text=value
            write(staging,'feed.xml',ET.tostring(rss,encoding='unicode',xml_declaration=True))
            write(staging,'robots.txt','User-agent: *\nAllow: /\nSitemap: '+renderer.absolute('sitemap.xml')+'\n')
        else:
            write(staging,'robots.txt','User-agent: *\nDisallow: /\n')
        # Complete in staging first: malformed sources never destroy a good build.
        destination=root/'dist'
        if destination.is_symlink():raise BuildError('dist 不得是符号链接')
        if destination.exists():shutil.rmtree(destination)
        staging.rename(destination)
        return {'articles':len(articles),'pages':len(routes)+1,'output':str(destination),'site_url':config['site_url'],'base_path':config['base_path']}
    finally:
        if staging.exists():shutil.rmtree(staging)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-path',default=os.environ.get('BLOG_BASE_PATH'))
    parser.add_argument('--site-url',default=os.environ.get('BLOG_SITE_URL'))
    args=parser.parse_args()
    try:
        result=build(base_path=args.base_path,site_url=args.site_url)
    except (BuildError,OSError,UnicodeError) as exc:
        print('构建失败：'+str(exc),file=sys.stderr)
        return 1
    print(f"构建完成：{result['articles']} 篇文章，{result['pages']} 个站点页面 → {result['output']}")
    if not result['site_url']:print('当前为本地预览配置；部署时会根据 Pages 地址生成 canonical、RSS 和 sitemap。')
    return 0


if __name__=='__main__':
    sys.exit(main())
