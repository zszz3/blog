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

命令生成草稿。编辑后将 `draft` 改为 `false`，提交文章文件夹。首页和归档自动更新，草稿不会进入正式页面、RSS 与搜索结果。

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
- 文档：`src/content/docs/`

GitHub 自动构建与服务器启用步骤见 [上线指南](docs/上线指南.md)。服务器部署尚需完成首次配置；构建成功不等于正式域名已经发布。

原文章的旧 `/posts/` 链接保留跳转。原主题许可证保存在根目录，新主题许可证见 `licenses/astro-theme-pure-LICENSE`。
