# AI Dev Template

AI 辅助开发的知识复用仓库 —— 收录技术栈模板、Prompt、MCP 配置、Skills 以及日常项目开发中积累的经验文档。

## 用途

- **技术栈选型模板**：记录经过验证的技术栈组合方案，新项目可直接参考
- **Prompt 模板**：沉淀高效的 AI 提示词，提升与 AI 协作的效率
- **MCP / Skills 配置**：可复用的 MCP Server 和 Skills 配置，快速搭建 AI 开发环境
- **经验文档**：项目开发中遇到的问题和解决方案，避免重复踩坑

## 兼容性

本仓库内容适配以下 AI 编码工具：

- **Cursor**
- **Claude Code**

## 目录结构

```
ai-dev-template/
├── frontend/                          # 前端项目
│   ├── tv/                            # TV 端
│   │   ├── webview/vue/               # Web 套壳 + Vue 技术栈
│   │   ├── native/                    # 原生开发 (Android TV Leanback, tvOS)
│   │   └── reactnative/              # React Native for TV
│   ├── mobile/                        # 移动端 (iOS, Android)
│   ├── admin/                         # 后台管理系统
│   ├── landing/                       # 落地页 / 营销页
│   ├── mini-program/                  # 小程序 (微信、支付宝、抖音)
│   └── desktop/                       # 桌面端 (Electron, Tauri)
├── backend/                           # 后端项目
│   ├── python/                        # Python (FastAPI, Django, Flask)
│   └── node/                          # Node.js (Express, NestJS, Nitro)
├── scripts/                           # 通用脚本工具
├── docs/                              # 学习笔记与方法论
├── devops/                            # 部署运维 (Docker, CI/CD, Nginx)
├── prompts/                           # Prompt 模板
├── mcp/                               # MCP 配置模板
└── skills/                            # Skills 配置模板
```

## 已有文档

### TV 端 — WebView + Vue

| 文件 | 格式 | 说明 |
|------|------|------|
| [`frontend/tv/webview/vue/cursor.mdc`](frontend/tv/webview/vue/cursor.mdc) | Cursor | Android TV WebView 开发规则与踩坑记录 |
| [`frontend/tv/webview/vue/CLAUDE.md`](frontend/tv/webview/vue/CLAUDE.md) | Claude Code | Android TV WebView 开发规则与踩坑记录 |

### 后台管理

| 文件 | 说明 |
|------|------|
| [`frontend/admin/nuxt-tech-selection.md`](frontend/admin/nuxt-tech-selection.md) | Nuxt.js 全栈管理后台技术选型方案 |

### Skills

| 文件 | 说明 |
|------|------|
| [`skills/ui-ux-pro-max.md`](skills/ui-ux-pro-max.md) | UI UX Pro Max — AI 设计智能 Skill，生成专业级 UI/UX 设计系统（配色、字体、风格、图表） |

### 学习笔记

| 文件 | 说明 |
|------|------|
| [`docs/ai-engineering-compound-growth.md`](docs/ai-engineering-compound-growth.md) | AI 工程化实践：从规范约束到复合增长（上下文工程、Subagent 架构、经验沉淀） |

### 通用脚本

| 文件 | 说明 |
|------|------|
| [`scripts/vue-build-deploy.py`](scripts/vue-build-deploy.py) | Vue 项目一键打包部署脚本（打包 → 压缩 → SSH 上传 → 备份 → 解压覆盖） |

## 使用方式

1. 浏览对应的模板或经验文档
2. 根据实际项目需求选用合适的方案
3. 将模板内容适配到你的 AI 编码工具中（Cursor Rules、Claude CLAUDE.md 等）

## 贡献

欢迎补充更多技术栈模板和经验文档，持续丰富知识库。
