#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a self-contained draft HTML article without overwriting an existing file."""
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from build import ROOT, BuildError, escaped, json_text, load_config, require_slug

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('--title',required=True)
    parser.add_argument('--description',default='请填写这篇文章解决的问题。')
    parser.add_argument('--category',default='agent-engineering')
    args=parser.parse_args()
    config=load_config(ROOT);require_slug(args.slug,'slug')
    if args.category not in config['categories']:raise BuildError('请先在 site.json 定义这个分类')
    if not args.title.strip():raise BuildError('标题不能为空')
    target=ROOT/'content/articles'/(args.slug+'.html')
    meta={'slug':args.slug,'description':args.description,'date':dt.date.today().isoformat(),'category':args.category,'tags':[],'topics':{},'draft':True}
    template=(ROOT/'templates/article.html').read_text(encoding='utf-8')
    replacements={'TITLE':escaped(args.title),'DESCRIPTION':escaped(args.description),'DATE':meta['date'],'CATEGORY':escaped(config['categories'][args.category]['name']),'META':json.dumps(meta,ensure_ascii=False,indent=2).replace('<','\\u003c')}
    template=re.sub(r'\{\{([A-Z]+)\}\}',lambda match:replacements[match.group(1)],template)
    with target.open('x',encoding='utf-8') as stream:stream.write(template)
    print('已创建草稿：'+str(target))
    print('写完并审核后，将 article-meta 中的 draft 改为 false，再构建发布。')

if __name__=='__main__':
    try:main()
    except (BuildError,FileExistsError) as exc:raise SystemExit(str(exc))
