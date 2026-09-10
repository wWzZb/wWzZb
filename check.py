#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check generated pages, local links, fragments, assets and search targets."""
import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT=Path(__file__).resolve().parent

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=[];self.h1=0;self.canonical=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='h1':self.h1+=1
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag in ('a','link') and attrs.get('href'):self.links.append(attrs['href'])
        if tag in ('script','img') and attrs.get('src'):self.links.append(attrs['src'])
        if tag=='link' and attrs.get('rel')=='canonical':self.canonical.append(attrs.get('href'))

def verify(dist,base_path=''):
    dist=Path(dist).resolve();base_path=base_path.rstrip('/')
    pages={};errors=[]
    for path in sorted(dist.rglob('*.html')):
        parser=Page();parser.feed(path.read_text(encoding='utf-8'));pages[path]=parser
        if parser.h1!=1:errors.append(f'{path.relative_to(dist)}: h1 数量为 {parser.h1}')
        if len(parser.ids)!=len(set(parser.ids)):errors.append(f'{path.relative_to(dist)}: 重复 id')
        if len(parser.canonical)>1:errors.append(f'{path.relative_to(dist)}: 重复 canonical')
    def resolve(url,source):
        parsed=urlsplit(url)
        if parsed.scheme or parsed.netloc:return None, None
        source_url='https://local.invalid'+base_path+'/'+source.relative_to(dist).as_posix()
        result=urlsplit(urljoin(source_url,url))
        path=unquote(result.path)
        if base_path and not path.startswith(base_path+'/'):
            raise ValueError(f'链接丢失部署前缀：{url}')
        local=path[len(base_path):].lstrip('/')
        target=(dist/local).resolve()
        if dist not in target.parents and target!=dist:raise ValueError(f'链接越出站点：{url}')
        if target.is_dir():target=target/'index.html'
        return target,unquote(result.fragment)
    for source,page in pages.items():
        for url in page.links:
            try:target,fragment=resolve(url,source)
            except ValueError as exc:errors.append(str(exc));continue
            if target is None:continue
            if not target.is_file():errors.append(f'{source.relative_to(dist)}: 缺少 {url}')
            elif fragment and target in pages and fragment not in pages[target].ids:errors.append(f'{source.relative_to(dist)}: 找不到锚点 {url}')
    index=json.loads((dist/'search-index.json').read_text(encoding='utf-8'))
    for entry in index['articles']:
        target,_=resolve(entry['url'],dist/'index.html')
        if not target or not target.is_file():errors.append('搜索目标不存在：'+entry['url'])
        if not entry['text'].strip():errors.append('搜索正文为空：'+entry['title'])
    if errors:raise ValueError('\n'.join(errors))
    return len(pages),len(index['articles'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-path',default='')
    args=parser.parse_args()
    try:
        pages,articles=verify(ROOT/'dist',args.base_path)
        print(f'检查通过：{pages} 个 HTML 页面、{articles} 篇搜索记录，内部链接与资源完整。')
    except (ValueError,OSError) as exc:
        print('检查失败：'+str(exc),file=sys.stderr);sys.exit(1)
