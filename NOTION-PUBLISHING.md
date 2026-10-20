# Notion → MkDocs Material → GitHub Pages

目标仓库：Caffreyfans/Caffreyfans.github.io，默认分支 hexo。

## 已检查的现有结构

2026-10-20 读取了 hexo 分支的文件树、package.json、_config.yml 和 .github/workflows/pages.yml。
该仓库已有 Hexo 博客，主题为 hexo-theme-matery，输出目录为 public。
现有 Pages 工作流在 hexo 推送后构建并发布 public。
_config.yml 还保留了部署到 master 的旧 Hexo deploy 配置，本方案不调用该命令。
连接器未允许读取 Actions workflows API；尚未核实仓库 Pages 设置页面或最近部署结果。

## 采用的方案

保留博客首页和文章，Notion 文档放在 https://caffreyfans.github.io/notion/。
扩展现有 pages.yml：先构建 Hexo，再构建 MkDocs，最后发布合并后的 public。
不要另外添加一条只发布 MkDocs 的 Pages 工作流，否则会替换整个站点。
如果 public/notion 已存在则停止，避免覆盖既有内容。

每小时第 23 分钟由 GitHub Actions 检查并重新构建；不是即时 webhook 同步。
定时运行可能延迟，只在默认分支生效。公共仓库长期无活动时，GitHub 可能停用定时工作流；
如停用，在 Actions 中重新启用，也可随时手动运行。
同步不提交 Notion 导出的正文到 Git 历史，正文仅存在于构建环境与公开站点。
每次全量重建，因此下一次成功部署会移除在 Notion 中删除的子页面。
同步或构建失败不会部署，新版上线前旧站点继续存在。
撤销集成权限并不会自动删除已上线内容；若误公开，应立即移除线上内容并重新部署，
且无法保证搜索引擎或访问者缓存中的内容被撤回。

## 操作步骤

1. 提供明确允许公开的 Notion 根页面链接。最好新建一个专用发布根页面，
   只将准备公开的内容放进去。子页面（包括以后新增的子页面）也会发布。
   与集成共享页面只是 API 访问授权，并不代表页面内容本身已获公开许可。
2. 在 Notion 创建内部集成，只开启读取内容权限，并仅将该发布根页面连接给它。
   不需要将 Notion 页面本身开启“发布到 Web”。聊天中的 Notion 连接不会自动给 Actions 提供凭证。
3. 打开 GitHub 仓库 Settings → Secrets and variables → Actions：
   - Repository secret `NOTION_TOKEN`：保存内部集成令牌。不要发送到聊天或写进代码。
   根页面已创建并经用户批准，工作流中已固定 NOTION_ROOT_PAGE_ID 和 NOTION_PUBLICATION_APPROVED，均为 3ff4fb93-f5cf-8137-8de5-f4faa853244e，无需再设置变量。
   页面：https://app.notion.com/p/3ff4fb93f5cf81378de5f4faa853244e
   请在该页面的连接设置中添加用于 Actions 的只读内部集成。
4. 从 hexo 创建配置分支，将本目录中的三个新增文件及 scripts 目录加入仓库。
   将本目录 `.github/workflows/pages.yml` 作为现有同名文件的修改版本审阅，
   不要删除其他工作流、source、themes、package.json 或锁文件。
   新增文件为 requirements-notion.txt、mkdocs.notion.yml、scripts/sync_notion.py。
   可将 `.notion-build/` 追加到原有 .gitignore，保留原有规则。
5. 先审阅差异。合并到 hexo 会触发构建并公开指定内容，所以要先完成公开范围核对。
   Settings → Pages 的 Source 应为 GitHub Actions；
   github-pages 环境若限制部署分支，应允许 hexo。
6. 合并后查看 Actions → Pages，或使用 Run workflow 选择 hexo。
   第一次成功后访问博客首页与 /notion/，检查文章链接、左侧页面树和搜索。
7. 修改 Notion 中一段测试文字，等下一次成功定时运行，确认更新。

## 文件与转换范围

- `scripts/sync_notion.py`：固定根页面遍历、分页、限流退避、只读 API、生成层级导航。
- `mkdocs.notion.yml`：中文界面、中英文搜索、左侧展开导航。
- `requirements-notion.txt`：明确固定的一组依赖版本，不声称是最新版本。
- `.github/workflows/pages.yml`：完整合并部署工作流。

当前支持段落、标题、列表、待办、代码、引用、callout、分栏、toggle、目录和结构性子页面。
toggle 展开显示；提及和普通超链接显示为文字，不追踪目标，富文本格式只保留加粗及斜体。
图片、附件、表格、公式、数据库、跨页面链接块及同步块暂不支持；出现时停止整个部署。
这是明确的转换限制，不会静默丢弃这些块。提供根页面后，应检查实际块类型并按需扩展。
不会查询整个工作区，也不会跟随普通链接或跨页面同步块读取其他内容。

## 回退

保留修改前 pages.yml 的提交。需要回退时恢复该文件并推送 hexo，
让原 Hexo 流程重新构建发布；这将移除 /notion/，保留博客。
删除或清空 NOTION_PUBLICATION_APPROVED 只会阻止新的同步发布，不会撤回已上线内容。

## 官方依据

- Notion API 版本：https://developers.notion.com/reference/versioning
- 子块读取与分页：https://developers.notion.com/reference/get-block-children
- GitHub Pages 自定义工作流：https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Material 搜索：https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/

使用 Notion-Version: 2026-03-11 及 GET /v1/pages/{id}、GET /v1/blocks/{id}/children。
Pages actions 选用已核对的官方部署指南中的 configure-pages@v5、
upload-pages-artifact@v4、deploy-pages@v4；这些与仓库当前文件中的版本号不同。
配置已推送到远程 notion-mkdocs-publishing 分支，尚未合并或启动部署。

## 本地验证

使用模拟的两级 Notion 页面通过了分页、子页面导航、公开确认拦截、
不支持块的拒绝，以及 MkDocs --strict 构建和搜索索引生成检查。
尚未进行真实 Notion API 同步、完整 Hexo 合并构建或 GitHub Pages 部署验证。
