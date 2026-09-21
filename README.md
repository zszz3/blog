# 我借此火 · 个人博客

基于 [Astro Theme Pure](https://github.com/cworld1/astro-theme-pure) 的完整页面布局，使用 AstroPaper 同款 Google Sans Code 字体。保留原有文章与图片，提供博客、文档、项目、友链、关于、归档、标签和全文搜索。

## 本地预览

使用 Node.js 22.12+ 和 pnpm 9：

```sh
pnpm install --frozen-lockfile
pnpm dev
```

## 写文章

文章与相对路径图片放在 `src/content/posts/`。已有文章使用的 `published`、`updated`、`image`、`tags`、`category` 和 `draft` 字段继续有效。

```sh
pnpm new-post "文章标题" --slug article-name
```

命令生成草稿。编辑后将 `draft` 改为 `false`，提交文章文件夹。博客按发布时间排列，文档按系列与章节排列。草稿不会进入正式页面、RSS 与搜索结果。

## 一份文章，两个入口

所有文章只放在 `src/content/posts/`，博客和文档不再有两套源文件。

```yaml
views: [blog, docs]
series: MySQL 学习笔记
order: 3
```

- `views: [blog]`：只在博客列表显示；不填写时默认如此，兼容旧文章。
- `views: [docs]`：只在文档目录显示。
- `views: [blog, docs]`：两边展示同一篇文章。
- `series`：文档的系列名称；未填写时归入「其他文档」。
- `order`：系列内部的章节顺序，非负整数，越小越靠前；缺省为 999。

所有文章使用唯一的 `/blog/文章标识` 地址。改变 `views`、系列名称、标题或章节顺序不会改变链接；移动源文件或改变目录名会改变链接。全文搜索、标签页和站点 RSS 均只收录一次；文档 RSS 从同一批文章中筛选 `docs`。

操作说明见 [写作指南](docs/authoring/writing.md)。

## 构建

```sh
pnpm build
python3 scripts/verify_site.py
pnpm preview
```

默认域名为 `https://wojiecihuo.cn`，可用环境变量 `SITE_URL` 覆盖。页面、字体、图片、RSS 和 Pagefind 搜索索引统一输出到 `dist/`。

## 调整内容

- 站点信息、导航和页脚：`src/site.config.ts`
- 首页：`src/pages/index.astro`
- 关于：`src/pages/about/index.astro`
- 颜色与排版：`src/assets/styles/app.css`
- 全部文章（含博客和文档）：`src/content/posts/`
- 发文操作说明：`docs/authoring/`
- 模板参考资料（不发布）：`docs/theme-reference/`

GitHub 到阿里云的自动发布已启用。将文章和图片提交或合并到 `main` 后，Actions 会自动构建并发布到 `https://wojiecihuo.cn`；`build` 和 `deploy` 都成功才表示网站已更新。维护与回退步骤见 [上线指南](docs/上线指南.md)。

原文章的旧 `/posts/` 链接保留跳转。原主题许可证保存在根目录，新主题许可证见 `licenses/astro-theme-pure-LICENSE`。
