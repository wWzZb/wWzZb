# 博客维护说明

博客仓库：https://github.com/wWzZb/wWzZb

网站地址：https://wwzzb.github.io/wWzZb/

仓库根目录的 `README.md` 用于 GitHub 个人简介，请保留；博客使用说明在本文件。推送到 `main` 后，GitHub Actions 会运行检查并发布网站。线上路径由 Pages 配置自动确定，本地预览仍可使用根路径。

# HTML 个人博客

独立 HTML 是文章的唯一正文源文件。自定义 Python 构建器读取元数据，生成首页、文章列表、分类、专题、标签页、全文搜索索引，再通过 GitHub Actions 发布到 GitHub Pages。

当前博客标题为临时名称「技术博客」。仓库、正式名称、自定义域名尚未确定，尚未向 GitHub 推送或公开发布。

## 本地运行

需要 Python 3.9 或以上。构建和预览不需要安装第三方库。

```sh
python3 build.py
python3 check.py
python3 serve.py
```

打开 `http://127.0.0.1:8780/`。修改文章后执行 `python3 build.py`，再刷新页面。预览服务只监听本机，不提供编辑后台，也不会自动上传内容。

`dist/` 是构建结果，会在每次成功构建后整体替换。不要在这里修改文章。源文件读取或校验失败时，原来的成功构建会保留。

## 内容结构

```text
content/articles/*.html       完整、可单独打开的文章
site.json                    网站名称、描述、分类和专题
templates/article.html       新文章模板
public/assets/               站点 CSS、图标与搜索逻辑
build.py                     HTML 解析与静态构建
check.py                     内部链接、锚点、资源和索引检查
new_article.py               创建草稿
serve.py                     本地预览
tests/                       构建器与搜索测试
.github/workflows/pages.yml  持续集成与 Pages 发布
dist/                        生成的静态站点，不提交到 Git
```

文章页的正文和原始 CSS 保持原样。构建器只在发布副本上加入站点导航和 SEO 信息；`dist/standalone/` 保存文章源文件的完整副本，读者可以下载。首页与专题页面的版式不要求文章采用统一模板。

## 新增文章

```sh
python3 new_article.py my-first-article --title '文章标题' --description '这篇文章解决什么问题'
```

脚本创建 `content/articles/my-first-article.html`，默认 `draft: true`。已有同名文件不会被覆盖。

直接编辑 HTML：标题放在唯一的 `<h1>`，正文放在唯一的 `<main>`；保留 UTF-8 和 viewport。文章应内联 CSS、图片等资源，或使用完整 HTTPS 地址，不依赖本机路径和旁边的文件。页面内引用 `#ref-1` 等锚点可正常使用。

每篇文章的 `<head>` 内有一段不可执行的 JSON：

```html
<script type="application/json" id="article-meta">
{
  "slug": "my-first-article",
  "description": "这篇文章解决什么问题。",
  "date": "2026-09-09",
  "updated": "2026-09-09",
  "category": "agent-engineering",
  "tags": ["上下文", "状态管理"],
  "topics": {"context-management": 5},
  "draft": true
}
</script>
```

- `slug`：稳定地址，只用小写英文、数字和连字符。修改后会改变文章 URL，现有外部链接需要另行迁移。
- `description`：用于列表、搜索和 SEO 的短介绍。
- `date` / `updated`：发布日期 / 更新日期，`updated` 可省略。日期不控制定时发布，发布与否只看 `draft`。
- `category`：一个主要分类，必须先在 `site.json` 中定义。
- `tags`：多个交叉检索标签，标签页自动生成。
- `topics`：可选的专题及阅读顺序，多个专题可以复用同一篇文章。一个专题内顺序不得重复。
- `draft`：必须显式填写布尔值。`true` 的文章不会进入任何公开页面、下载文件或搜索索引。

标题直接读取 `<h1>`，不用在 JSON 里重复维护。JSON 内容中的 `<` 建议写作 `\u003c`，尤其不要直接写入 `</script>`。

完成内容核对后，把 `draft` 改为 `false`，执行构建与检查，再提交。

## 分类与专题

在 `site.json` 的 `categories` 或 `topics` 中增加对象，再在文章元数据中引用对应标识。

分类是一篇文章的主要领域。专题是人为策划的阅读路径，可以跨分类；它只引用独立文章，不复制正文。标签是更细的关键词，可以跨分类和专题。

没有已发布文章的分类或专题暂不显示。新增、删去或设为草稿后，相关页面和搜索记录随下一次构建更新。

## 搜索

构建器从 `<main>` 中提取纯文本与标题，不把 CSS、JSON 元数据或博客导航写进索引。浏览器读取同站点的 `search-index.json`，在本地搜索标题、标签、章节标题、摘要与全文。

支持中文子串、多关键词空格分隔（AND）、英文大小写与全角字符归一化，以及分类过滤。搜索结果带正文摘录。用户输入与结果通过 DOM 文本节点呈现，不直接插入 HTML。

这是普通全文子串匹配，不是语义检索。文章规模大幅增长后，可再引入分词、分片索引或其他搜索引擎。请通过预览服务或正式网址使用搜索；直接双击站点首页时，浏览器可能禁止读取本地 JSON。

## 检查与测试

搜索测试使用 Node.js 18 或以上；日常构建不需要 Node。

```sh
python3 -m unittest discover -s tests -v
node --test tests/search.test.cjs
python3 build.py
python3 check.py
```

测试覆盖草稿隔离、源正文保持、失效构建保护、删除后重建、元数据验证、根域名与仓库子路径、搜索排序、中文搜索和多关键词过滤。`check.py` 不联网，只检查已生成站点的本地链接、资源和锚点。

## GitHub Pages

仓库名称确认后，在独立仓库根目录放置本项目文件。不要把上层工作目录、原始聊天记录或其他项目一起上传。

1. 在 GitHub 创建或选择仓库，使用 `main` 分支。
2. 在仓库 **Settings → Pages → Build and deployment** 中，选择 **GitHub Actions**。
3. 推送本项目。工作流先运行测试、构建与链接检查，再上传 `dist/` 并部署。
4. 在 Actions 的部署结果或 Settings → Pages 查看实际网址。

PR 只构建与测试，不部署。`main` 的推送和手动运行执行部署。测试失败不会进入部署作业。

工作流通过 `actions/configure-pages` 提供的 `base_url` 和 `base_path` 自动生成正确链接，支持：

- 用户站点：`https://USERNAME.github.io/`
- 项目站点：`https://USERNAME.github.io/REPOSITORY/`
- 已配置的自定义域名：`https://blog.example.com/`

正式地址存在时，构建器生成 canonical、Open Graph、RSS、sitemap 与允许抓取的 robots.txt。未配置地址的本地预览不会伪造域名，不生成 RSS / sitemap，并设置禁止抓取。

手动检查仓库子路径可以使用：

```sh
python3 build.py --base-path /personal-blog --site-url https://USERNAME.github.io/personal-blog
python3 check.py --base-path /personal-blog
```

完成后执行 `python3 build.py` 恢复本地根路径预览。正式工作流使用 GitHub 返回的地址，不需要手动写死用户名。

## 自定义域名

域名尚未选定，不会自动注册域名或修改 DNS。

域名确定后，在 GitHub Pages 设置中配置已持有的域名，再按 GitHub 官方说明配置 DNS。推荐先在 GitHub 验证域名所有权，等待 DNS 检查和 HTTPS 证书就绪后启用 HTTPS。

此项目使用自定义 Actions 工作流，**生成一个 CNAME 文件不能代替 Pages 设置和 DNS 配置**。GitHub 文档明确说明这种发布方式不需要 CNAME 文件，而且现有 CNAME 文件会被忽略。完成域名设置后重新运行工作流，让构建器使用新的 Pages 地址生成链接和索引。

官方依据：

- [自定义 Pages 工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [管理自定义域名](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [验证域名](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages)

## 内容进入博客之前

从 ChatGPT、Codex、项目或研究取得素材后，先提炼技术主题并核对依据，再写成面向陌生读者的独立文章。原始聊天、内部资料和未经核对的推测不自动导入公开文章。文章完成后，用元数据将它归入分类和专题；构建器负责生成入口和索引。

本项目只实现整理完成后的内容构建与发布链路，不会自动读取其他聊天或代表作者发布未经确认的新内容。

## 网站样式

当前使用 EveLab Insight 设计系统。配色、组件和独立文章样式的修改位置见 [样式说明](design/README.md)。
