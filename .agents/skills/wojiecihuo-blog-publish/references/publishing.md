# 发布与验收

当前仓库内的 `.github/workflows/deploy.yml`、`scripts/deploy.sh`、`scripts/package-release.py`、`deploy/release.py` 和 `docs/上线指南.md` 是发布机制的事实来源。以下命令在已核对 remote 的博客仓库中运行；操作前替换示例值，不从其他任务照搬提交号或运行号。

## 提交前

```sh
git status --short
git remote -v
git fetch origin main
git log --oneline origin/main..HEAD
git diff --stat
```

确认 remote 对应 `zszz3/blog`，且当前分支相对 `origin/main` 的所有待发布提交都属于授权范围。仅挑选文件提交还不够：推送 `HEAD` 会同时带上该分支未发布的祖先提交。若有无关提交或他人未完成改动，从最新 `origin/main` 建独立 `codex/` 分支/worktree，只移入本次内容。同步上游后，如果待发布内容发生变化，重新做必要检查。

正式发布前把文章设为 `draft: false`，在最终待提交状态运行构建与链接检查。仅存草稿则保留 `true`。先检查差异，再按明确路径暂存，避免 `git add .` 带入不相关内容、源文档或临时素材。

## 发布方式

用户明确要求正式发布，且当前仓库规则允许直接提交主分支时：提交本次内容，然后使用普通快进推送 `git push origin HEAD:main`。推送被拒绝时先检查远端变化，合并/重放适当提交并重新检查，不使用强制推送。

用户要求 PR 或仓库要求 PR 时，推送工作分支并创建 PR；PR 检查通过并不等于上线。按已获授权的合并范围继续工作；否则交付 PR 并说明仍未发布。若环境要求保存 PR 附件，创建后附加到当前任务。

用户只要求本地修改、草稿或预览时，停在对应状态，不自行转成正式发文。若用户明确要求把草稿保存到 GitHub，可推送 `draft: true` 的原稿，但需注意公开仓库仍可读取原文。

## 跟踪本次提交

记录实际推送到 `main` 的提交：直接推送通常为本地 `HEAD`，PR 合并则使用实际合并后的提交。用该提交精确查找运行：

```sh
git rev-parse HEAD
gh run list --repo zszz3/blog --workflow deploy.yml --branch main --commit ACTUAL_COMMIT_SHA --limit 5 --json databaseId,headSha,status,conclusion,url
gh run watch ACTUAL_RUN_ID --repo zszz3/blog --exit-status --interval 30
gh run view ACTUAL_RUN_ID --repo zszz3/blog --json headSha,status,conclusion,jobs,url
```

`ACTUAL_COMMIT_SHA` 与 `ACTUAL_RUN_ID` 是占位说明，执行时替换。通过工具分段等待，保留向用户更新进度的机会。不按“列表第一条是绿色”判断自己的发布。

确认 `build` 成功，`deploy` 成功且其中 `Publish complete release` 的结论为 `success`。工作流会在该提交已不是最新 `main` 时跳过实际传输，所以单看 job 绿色仍不够。按实际 deploy job ID 查看日志：

```sh
gh run view ACTUAL_RUN_ID --repo zszz3/blog --job ACTUAL_DEPLOY_JOB_ID --log
```

正常日志包含上传/复用文件数量和服务器返回的发布回执，`release` 格式为 `运行序号-尝试序号-完整提交SHA`；应为 `published`，或重跑已上线版本时合理的 `unchanged`。`skipped` 不是这次提交已上线。日志若显示被更新提交取代，检查新的主分支是否仍包含本次内容，并跟踪实际发布的新运行，不把旧运行算作成功。

## 正式站点验收

部署完成后检查 `https://wojiecihuo.cn`：

- 打开文章真实 URL，确认新增或修改的具体文字已出现，而不只是 HTTP 200。
- 确认封面、正文图片和附件可用；对应 `/blog/` 或 `/docs/` 列表入口正确。旧文未进入首页最近文章列表不表示发布失败。
- 搜索能找到文章，`/search.json` 与 `/rss.xml` 包含正确地址；`docs` 文章同时检查文档入口和其 RSS，路径以当前页面链接/源码为准。
- 文章被撤为草稿时，检查生产页面、列表、搜索和 RSS 均已移除；只确认“文件已推送”不够。

日常验证用 Actions 回执和正式网站即可。部署私钥保存在 GitHub Secrets，不为普通发文索要或导出私钥，也不假设开发机有长期可用的 SSH 身份。

## 失败与回退

构建失败时查看 `gh run view ACTUAL_RUN_ID --repo zszz3/blog --log-failed`，修复内容或链接后再提交。部署失败时，先核对是否跳过、开关未启用、网络失败或归档验证失败；不要把“未上线”报告成“正在缓存”。失败的构建/上传/校验不会自动替换现有版本。

生产默认使用校验清单和增量传输，不改成每次上传整站压缩包。已确认的网络瞬时失败可以重跑失败任务；同一原因重复失败且没有新证据时，停止重复重跑并给出阻塞。缺少账号权限或凭证时完成本地内容与验证，报告发布所缺条件，不另建访问凭证或扩大服务器权限。

用户要求回退，或当前任务已有明确回退授权时，可运行：

```sh
gh workflow run deploy.yml --repo zszz3/blog --ref main -f operation=rollback -f release=previous
```

也可使用已核实的历史版本编号。先确认目标版本；不要通过真实回退来测试日常发文。跟踪新触发的运行，核对 `rollback` job、回执和正式网站。服务器回退不修改 Git 原稿；下一次 `main` 提交仍会发布主分支内容，需要时另行修正源码。

只有故障确实涉及基础设施且用户要求修复时，才深入阅读上线指南的服务器部分。现有服务器还服务其他应用，不能为了发文占用 80 端口或替换现有代理。
