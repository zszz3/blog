---
title: 写文章：本地与 GitHub
description: Markdown、图片、草稿与发布的日常操作。
order: -20
publishDate: 2026-09-12
tags: [写作, GitHub]
---

## 一篇文章一个文件夹

文章放在 `src/content/posts/`，图片与文章放在同一个目录：

```text
src/content/posts/my-first-post/
  index.md
  example.png
```

可以在本地写完后提交，也可以在 GitHub 网页上传这些文件。目录名决定文章网址，发布后尽量保持不变。

## 填写文章信息

```yaml
---
title: 我的第一篇文章
published: 2026-09-12
description: 一句话介绍这篇文章。
image: ./example.png
tags: [Java, 学习笔记]
category: 技术
draft: false
---
```

正文写在第二条 `---` 后面。封面可留空，正文图片写作 `![图片说明](./example.png)`。

未完成时使用 `draft: true`。草稿可以提交到仓库，但不会出现在正式网站、搜索索引或 RSS 中。

## 本地预览

运行 `pnpm dev`，打开终端显示的本地地址即可预览。运行 `pnpm new-post "文章标题" --slug article-name` 可以生成一篇草稿。

## 提交与发布

确认内容后把 `draft` 改为 `false`，提交到 `main`。GitHub Actions 会检查文章并构建网站；服务器部署启用后，构建成功的版本才会替换线上版本。

发布结果在 GitHub 的 Actions 页面查看。失败时原网站会继续保留。

## 更新已有文章

直接修改原文件，必要时增加 `updated: 2026-09-13`。使用同一个目录，文章网址保持不变。
