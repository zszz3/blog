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
views: [blog, docs]
series: Java 学习笔记
order: 1
draft: false
---
```

正文写在第二条 `---` 后面。封面可留空，正文图片写作 `![图片说明](./example.png)`。

未完成时使用 `draft: true`。草稿可以提交到仓库，但不会出现在正式网站、搜索索引或 RSS 中。

## 博客和文档共用文章

两种入口都读取 `src/content/posts/`，不要复制同一篇文章到另一个目录。

- `views: [blog]`：普通博客文章。旧文件不填写 `views` 时默认使用此值。
- `views: [docs]`：只列入文档目录。
- `views: [blog, docs]`：博客与文档同时展示。

文档按 `series` 分组，按 `order` 从小到大排序。不填写系列时归入「其他文档」，不填写顺序时默认使用 999。博客按原始发布日期排列。

修改正文、标题、展示位置或章节排序只需改这一份文件。文章地址始终为 `/blog/文章标识`；搜索与站点订阅只收录一次。文档目录和文档订阅指向同一个地址。

## 本地预览

运行 `pnpm dev`，打开终端显示的本地地址即可预览。运行 `pnpm new-post "文章标题" --slug article-name` 可以生成一篇草稿。

## 提交与发布

确认内容后把 `draft` 改为 `false`，提交到 `main`。GitHub Actions 会检查文章并构建网站；服务器部署启用后，构建成功的版本才会替换线上版本。

发布结果在 GitHub 的 Actions 页面查看。失败时原网站会继续保留。

## 更新已有文章

直接修改原文件，必要时增加 `updated: 2026-09-13`。使用同一个目录，文章网址保持不变。
