---
title: 上传从飞书导出的文章
description: 把导出的 Markdown 与图片整理为一篇博客。
order: -19
publishDate: 2026-09-12
tags: [写作, 飞书, Markdown]
---

## 准备 Markdown 和图片

在飞书完成写作，自己导出为 Markdown。拿到文件后，把正文和它引用的图片目录一起保存，保持原有的相对路径关系。

## 放进文章目录

为文章新建一个稳定的文件夹，例如 `src/content/posts/agent-notes/`，将 Markdown 命名为 `index.md`。导出文件中引用的本地图片也放在这个文件夹内。

如果图片地址仍是飞书的临时链接，请先把图片保存到本地，再把正文引用改为相对路径。否则链接过期后，博客可能无法显示图片。

## 补充文章信息

在正文最前面添加：

```yaml
---
title: 我的 Agent 笔记
published: 2026-09-12
description: 这篇文章的简短介绍。
tags: [Agent]
category: 技术
draft: true
---
```

先使用草稿状态检查图片、代码、表格和公式。内容确认后，将 `draft` 改为 `false`。

## 上传 GitHub

把整个文章文件夹提交到主分支，后续检查、生成搜索索引与站点发布走同一条自动流程。

以后更新这篇文章时，继续使用原文件夹，替换正文与需要更新的图片即可。
