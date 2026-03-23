# AIT CLI 设计文档

> AI 开发配置管理工具 — 跨机器、跨项目复用 Rules、Skills、MCP、模板

## 1. 目标

提供一个 CLI 工具 `ait`，将 `ai-dev-template` 仓库作为中心存储，通过 symlink 机制实现：

- 全局安装：clone 仓库后一键 symlink 所有 rules/skills 到 `~/.claude/` 等目标路径
- 项目配置：通过 profile 或手动选择，为项目配置所需的 AI 开发资源
- 换机复用：新电脑 clone + `ait install` 即可恢复全部配置

## 2. 管理范围

| 类型 | 仓库源路径 | 全局安装目标 | 项目安装目标 | 安装方式 |
|---|---|---|---|---|
| Claude Code rules | `rules/claude/` | `~/.claude/rules/` | `.claude/rules/` | symlink |
| Cursor rules | `rules/cursor/` | — | `.cursor/rules/` | symlink |
| Skills | `skills/` | `~/.claude/skills/` | `.claude/skills/` | symlink |
| CLAUDE.md 模板 | `templates/` | — | `./CLAUDE.md` | copy |
| MCP 配置 | `mcp/` | — | `.claude/mcp.json` | merge |

## 3. 技术栈

| 组件 | 选型 |
|---|---|
| 语言 | Python 3.10+ |
| CLI 框架 | typer |
| 依赖管理 | uv |
| Frontmatter 解析 | python-frontmatter |
| YAML 解析 | PyYAML |
| 安装方式 | `uv tool install` / `pipx` |

## 4. 仓库目录结构

```
ai-dev-template/
├── rules/
│   ├── claude/                    # Claude Code rules (.md)
│   │   ├── vue-use-eui.md
│   │   ├── server-security.md
│   │   ├── git-security.md
│   │   └── python-code-style.md
│   └── cursor/                    # Cursor rules (.mdc)
│       └── tv-webview-vue.mdc
├── skills/                        # Claude Code skills (.md)
│   └── ui-ux-pro-max.md
├── templates/                     # CLAUDE.md 项目模板
│   ├── tv-webview-vue.md
│   └── nuxt-admin.md
├── mcp/                           # MCP 配置片段 (.json)
│   └── context7.json
├── profiles/                      # Profile 定义
│   ├── vue-admin.yaml
│   └── fastapi.yaml
└── cli/                           # CLI 工具源码
    ├── pyproject.toml
    └── src/
        └── ait/
            ├── __init__.py
            ├── main.py            # typer app 入口
            ├── commands/
            │   ├── install.py
            │   ├── use.py
            │   ├── list_cmd.py
            │   ├── update.py
            │   ├── add.py
            │   ├── remove.py
            │   ├── sync.py
            │   ├── status.py
            │   ├── profiles.py
            │   └── show.py
            └── core/
                ├── config.py      # 路径常量、配置
                ├── linker.py      # symlink 创建/清理
                └── registry.py    # 扫描仓库、解析 frontmatter
```

## 5. 资源文件 Frontmatter 规范

### Markdown 资源（rules、skills、templates）

```markdown
---
name: vue-use-eui
description: Vue 项目统一使用 @danweiyuan/eui 组件库
type: claude-rule
tags: [vue, ui, eui]
version: 1.0.0
author: chances
---

（正文内容）
```

**type 可选值**：`claude-rule` | `cursor-rule` | `skill` | `template` | `mcp`

### MCP 配置（JSON）

```json
{
  "_meta": {
    "name": "context7",
    "description": "Context7 文档查询服务",
    "type": "mcp",
    "tags": ["docs", "context"],
    "version": "1.0.0",
    "author": "chances"
  },
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic/context7-mcp"]
    }
  }
}
```

安装时去掉 `_meta` 字段，将 `mcpServers` 内容合并到目标 `mcp.json`。

## 6. Profile 定义

```yaml
# profiles/vue-admin.yaml
name: vue-admin
description: Vue 3 管理后台项目配置
author: chances
version: 1.0.0

rules:
  claude:
    - vue-use-eui
    - server-security
    - git-security
  cursor:
    - tv-webview-vue

skills:
  - ui-ux-pro-max

templates:
  - nuxt-admin

mcp:
  - context7
```

通过资源的 `name` 字段关联。Profile 查找基于**文件名**（`ait use vue-admin` → `profiles/vue-admin.yaml`），YAML 内的 `name` 字段用于展示。

## 7. CLI 命令

### 全局操作

```bash
ait install                    # clone 仓库到 ~/.ai-dev-template/
                               # symlink 全局 rules 和 skills

ait update                     # git pull 更新仓库
                               # 显示更新了哪些文件

ait list                       # 列出所有资源
ait list --type claude-rule    # 按类型筛选
ait list --tag vue             # 按标签筛选

ait status                     # 全局安装状态：已安装、断链检测

ait profiles                   # 列出所有可用 profile

ait show <name>                # 查看资源详情（frontmatter + 内容预览）
```

### 项目级操作

```bash
ait use <profile>              # 按 profile 配置当前项目

ait add <name>                 # 添加单个资源到当前项目

ait remove <name>              # 移除资源（删除 symlink）

ait sync                       # 根据 .ai-rules.json 重建所有链接
```

## 8. 冲突与边界处理

### `ait use` 重复执行

`ait use` 采用**替换策略**：
1. 读取已有 `.ai-rules.json`（如存在）
2. 移除旧 profile 中有但新 profile 中没有的资源（删除 symlink，MCP 按 `merged_keys` 移除）
3. 安装新 profile 的所有资源
4. 覆盖写入新的 `.ai-rules.json`

### `ait add` 与已有 profile 的关系

`ait add` 在已有 profile 的项目上执行时，保留 `profile` 字段不变，将新资源追加到 `resources` 列表。

### `ait remove` 各模式行为

| mode | 行为 |
|---|---|
| `symlink` | 删除 symlink 文件 |
| `copy` | 删除目标文件（提示确认，因为用户可能已修改） |
| `merge` | 从 `mcp.json` 中移除 `merged_keys` 记录的 key |

### 多 template 处理

一个 profile 只允许声明**一个 template**。CLI 校验时如果发现多个则报错。

### `--force` 标志

所有涉及覆盖的操作（`use`、`add`、`sync`）支持 `--force` 跳过确认提示。默认交互式询问。

## 9. 项目级 `.ai-rules.json`

由 CLI 在**目标项目目录**（非本仓库）自动生成和维护。

```json
{
  "profile": "vue-admin",
  "resources": [
    {
      "name": "vue-use-eui",
      "type": "claude-rule",
      "version": "1.0.0",
      "target": ".claude/rules/vue-use-eui.md",
      "mode": "symlink"
    },
    {
      "name": "nuxt-admin",
      "type": "template",
      "version": "1.0.0",
      "target": "CLAUDE.md",
      "mode": "copy"
    },
    {
      "name": "context7",
      "type": "mcp",
      "version": "1.0.0",
      "target": ".claude/mcp.json",
      "mode": "merge",
      "merged_keys": ["context7"]
    }
  ],
  "repo": "~/.ai-dev-template",
  "updated_at": "2026-03-23T10:00:00"
}
```

- `profile` 为 `null` 表示纯手动 add
- `mode`：`symlink` | `copy` | `merge`
- MCP 资源额外记录 `merged_keys`，用于 `ait remove` 时精确移除

## 10. 核心流程

### `ait install`

1. 检查 `~/.ai-dev-template/` 是否存在
   - 不存在 → `git clone` 仓库到该目录
   - 已存在 → `git pull` 更新
2. 支持 `--repo-path` 指定已有的本地仓库路径（避免重复 clone）
3. 扫描仓库所有资源，解析 frontmatter，构建索引
4. 将 `rules/claude/` 下所有文件 symlink 到 `~/.claude/rules/`
5. 将 `skills/` 下文件 symlink 到 `~/.claude/skills/`
6. 输出安装摘要

### `ait use <profile>`

1. 读取 `profiles/<profile>.yaml`（按文件名匹配）
2. 校验所有引用的资源名是否存在，校验 template 不超过 1 个
3. 如果已有 `.ai-rules.json`，先清理旧 profile 中多余的资源
4. 对每种类型执行安装：
   - `claude-rule` → symlink 到 `.claude/rules/`
   - `cursor-rule` → symlink 到 `.cursor/rules/`
   - `skill` → symlink 到 `.claude/skills/`（项目级）
   - `template` → copy 到项目根目录 `CLAUDE.md`（已存在则提示确认，`--force` 跳过）
   - `mcp` → 去掉 `_meta`，合并到 `.claude/mcp.json`（已有 key 不覆盖），记录 `merged_keys`
5. 生成 `.ai-rules.json`
6. 将 `.ai-rules.json` 加入 `.gitignore`（幂等检查，已存在则不重复追加）
7. 输出安装结果

### `ait add <name>`

1. 在仓库中查找资源（按 frontmatter `name` 匹配）
2. 找不到则报错并列出相似名称
3. 按资源 `type` 确定目标路径和安装 mode
4. 执行安装（symlink/copy/merge）
5. 更新 `.ai-rules.json`（追加到 `resources`，保留已有 `profile`）

### `ait remove <name>`

1. 读取 `.ai-rules.json`，找到对应资源
2. 按 mode 执行清理：
   - `symlink` → 删除 symlink
   - `copy` → 提示确认后删除（`--force` 跳过）
   - `merge` → 从 `mcp.json` 中移除 `merged_keys` 对应的 key
3. 从 `.ai-rules.json` 中移除该资源

### `ait sync`

1. 读取当前目录 `.ai-rules.json`
2. 检查 repo 路径是否存在（不存在则提示先 `ait install`）
3. 逐个资源重建：
   - `symlink` → 重新创建链接（已存在则跳过）
   - `copy` → 跳过（已存在则不覆盖）
   - `merge` → 检查 `mcp.json` 缺失的 key，补充
4. 输出同步结果

### `ait status`

1. 检查全局安装状态（`~/.ai-dev-template/` 是否存在、git 是否最新）
2. 扫描 `~/.claude/rules/` 和 `~/.claude/skills/` 中的 symlink
3. 检测断链（symlink 目标不存在）
4. 如果当前目录有 `.ai-rules.json`，同时显示项目级状态

## 11. 安装方式

```bash
# 开发模式
cd ai-dev-template/cli
uv sync
uv run ait --help

# 全局安装
cd ai-dev-template/cli
uv tool install .

# 或通过 pipx
pipx install ./cli
```

## 12. 迁移计划

当前仓库需要重组才能适配 CLI。迁移步骤：

1. 创建 `rules/claude/` 目录，将 `~/.claude/rules/` 中的个人 rules 复制进来
2. 创建 `rules/cursor/` 目录，将 `frontend/tv/webview/vue/cursor.mdc` 移入
3. 创建 `templates/` 目录，将现有 CLAUDE.md 模板移入（如 `frontend/tv/webview/vue/CLAUDE.md`）
4. 创建 `profiles/` 目录，编写初始 profile YAML
5. 为所有资源文件添加 frontmatter 元数据
6. 创建 `cli/` 目录，实现 CLI 工具

现有 `frontend/`、`docs/`、`scripts/` 等目录保持不变，CLI 不管理这些内容。

## 13. 前置验证

实现前需确认：
- **Claude Code 是否跟随 symlink**：在 `~/.claude/rules/` 中创建一个 symlink 指向测试文件，验证 Claude Code 能正确加载
- 如果不支持 symlink，回退到 copy 模式（但失去自动同步优势）

## 14. 设计约束

- macOS 优先，symlink 无限制
- 个人使用场景，不考虑多用户协作
- 仓库删除则所有 symlink 失效，`ait status` 可检测断链
- template 用 copy 因为 CLAUDE.md 通常需按项目修改
- mcp 用 merge 避免覆盖已有配置
- MCP 不做全局安装（全局 MCP 配置因环境差异大，适合手动管理）
- symlink 资源始终指向最新版本，copy/merge 资源是安装时的快照
- `ait install` 支持 `--repo-path` 复用已有 clone，避免重复下载
