# 内容与图片规则

## 新建与更新

新建文章使用仓库已有脚本，避免重复维护模板：

```sh
pnpm new-post "文章标题" --slug article-name
```

脚本生成 `src/content/posts/article-name/index.md`，默认 `draft: true`；同名目录存在时会拒绝覆盖。目录名支持文字、数字、横线和下划线，建议使用稳定、简短的小写英文名。示例中的标题、目录、日期和标签均需替换为当前文章的实际值。

更新旧文时先按标题或正文定位原文件。旧文可能不是 `index.md`，例如 `MySQL/MySQL锁.md`；不要为了统一目录格式而重命名。保留原 `published`/`publishDate`，有实际内容更新时填写 `updated` 或更新已有 `updatedDate`。兼容字段同时存在时，`publishDate` 优先于 `published`，`updatedDate` 优先于 `updated`，避免写入互相冲突的值。

## Frontmatter

```yaml
---
title: "文章标题"
published: 2026-09-22
description: "一句话说明文章解决什么问题。"
image: "./cover.webp"
tags: [Agent, 学习笔记]
category: 技术
views: [blog]
draft: true
---
```

| 字段 | 使用规则 |
| --- | --- |
| `title` | 必填、非空。含冒号等 YAML 字符时加引号。 |
| `published` | 必须提供 `published` 或 `publishDate`；新文按实际发布日期，默认采用上海时区当天，不改旧文日期来置顶。 |
| `description` | 根据实际正文写简介，不添加正文没有的结论。 |
| `image` | 相对路径指向确实存在的本地封面；没有时可省略或留空，不能写不存在的占位路径。 |
| `tags` | 字符串数组，尽量沿用已有标签拼写和大小写；页面自动生成标签及对应链接。 |
| `category` | 单个分类字符串；空值会归入“未分类”。 |
| `views` | `[blog]`、`[docs]` 或 `[blog, docs]`；缺省为 `[blog]`。 |
| `series` / `order` | 文档系列名称和非负整数章节顺序；缺省为“其他文档”与 999。 |
| `draft` | 明确发布时改为 `false`；仅预览/草稿保持 `true`。缺省实际是 `false`，不要漏写草稿标记。 |

不要把 `docs/authoring/` 示例中的负数 `order` 搬进文章集合，文章 schema 要求非负整数。当前筛选只排除草稿，不排除未来日期；需要预约发布时，另行处理定时需求。

文档入口配置示例：

```yaml
views: [blog, docs]
series: Agent 学习笔记
order: 2
```

`views: [docs]` 只影响目录归属，不表示私密。文章仍是公开页面，站点搜索、标签和 RSS 也会收录。其正式地址仍为 `/blog/<文章标识>`。

文章标识由相对 `src/content/posts/` 的路径去掉 `.md`/`.mdx`、去掉末尾 `/index`、转为小写得到。例如 `agent-notes/index.md` → `/blog/agent-notes`；`MySQL/MySQL锁.md` → `/blog/mysql/mysql锁`。用生成的 canonical 或站内链接确认最终 URL，不自行改成 `/docs/文章名`。

## 封面与正文图片

建议目录：

```text
src/content/posts/article-name/
  index.md
  cover.webp
  images/
    architecture.png
```

正文引用 `![架构说明](./images/architecture.png)`。当前封面优先级是显式 `heroImage`（包括 schema 从 `image` 转换的值），其次是正文第一张 Markdown 图片；同时有 `heroImage` 与 `image` 时，前者优先。已有封面不要无故替换。

用户希望新文章配图，选图偏好二次元插画。优先使用用户提供或已允许使用的配图；正文中已有合适图片也可明确设为封面。另找素材时确认可用于个人博客并保留必要署名，生成图片则按当前可用工具操作。没有可用素材时先完成文章整理，说明待补封面，不假装配图已完成。技术图应保持信息清晰。

封面保存在文章目录并写相对路径，确保构建时能被 Astro 解析。不要把 Pixiv 作品页、飞书预览页、登录态链接或本机绝对路径当作图片地址。导入的临时图片链接应保存为随文素材并替换引用。保留清晰度的前提下减少图片体积；增量发布仍需要完整传输新增图片。

## 导入外部文档

- **Markdown / 飞书导出**：优先保留正文和图片目录关系；补齐 frontmatter，清理导出产生的临时路径。飞书链接需要读取内容时用当前环境的飞书文档能力；只有导出文件时直接处理文件。
- **Word / PDF**：用户要求变成文章时，提取正文、图片、代码、表格和公式后转换为 Markdown，利用当前环境相应文档工具检查，不能只改扩展名。扫描件或提取不可靠的段落明确标注待核对，不编造缺失内容。
- **仅提供原文件下载**：按用户要求把可公开原文件放在 `public/downloads/<稳定目录>/`，文章引用 `/downloads/<稳定目录>/文件名.pdf` 等路径。原文件是否公开取决于当次要求，转换成文章不自动附带原文件。

导入完成后对照源文检查遗漏和格式。若用户只要求上传，不主动重写技术内容；需要内容润色或重构时再按对应任务处理。

## 文章检查重点

核对标题和目录、简介、标签、日期、草稿状态及 `views`；确认图片/附件都已纳入本次提交。构建并运行仓库链接检查后，查看目标文章的封面、正文图片、代码、表格、公式和章节链接。检查新文章在搜索/RSS 中只出现一次；文档 RSS 仅包含 `docs` 文章。草稿不得进入生产产物。
