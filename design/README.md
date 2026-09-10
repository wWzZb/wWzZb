# EveLab 样式适配

样式依据：用户提供的 `evelab-insight-export.zip`，规范存档在 [evelab-spec.md](evelab-spec.md)。只采用颜色、字体栈、间距、圆角和组件外观，不引入展示页面的 React、Babel、第三方脚本或业务内容。

- `public/assets/design-tokens.css`：原设计的颜色、字号、间距、圆角、阴影变量。
- `public/assets/site.css`：博客首页、列表、分类、专题、搜索等页面的组件样式。
- `content/articles/*.html`：每篇文章内嵌设计变量和文章样式，下载后可独立打开。
- `templates/article.html`：新增文章使用同一套内嵌样式。
- `build.py`：输出站点样式引用及文章顶部导航。

主要样式：`#1fc8d2` 青色、`#f8f8f7` 背景、白色卡片、20px 卡片圆角、胶囊导航/按钮/输入框、轻阴影。专题和提示框使用浅青色，搜索命中使用浅琥珀色。

两处为阅读体验作了调整：青色按钮用深色文字，正文链接使用深青色，改善小字对比度；去掉 Google Fonts 在线导入，保留原字体栈，并使用苹方、微软雅黑等本机字体回退。中文长文保留较宽行距。

修改后运行 `python3 build.py`，再刷新预览页。文章正文样式在独立 HTML 内；只修改站点 CSS 不会改变下载文章的样式。
