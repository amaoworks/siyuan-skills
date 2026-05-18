# 思源笔记 Skills Collection

思源笔记（SiYuan Note）技能集合，采用分层设计提供基础知识和专用工具。

这些 skills 遵循 [Claude Skills 规范](https://github.com/anthropics/skills)，可被 Claude Code 和其他兼容 agent 使用。

## ⚠️ 重要更新

### 2026-05-18

- **🔧 统一 API 客户端**：新增 `_shared/siyuan_client.py`，提供 `SiyuanClient` 类封装所有常用端点。所有 skill 调用 API 必须经过它，不再手写 `requests.post` 或 curl。详见下方「API 调用约定」一节。
- **🚨 硬约束前置**：`siyuan/SKILL.md` 顶部加入「调用 API 的硬约束」，`references/api.md` 的 curl 示例整节替换为 Python 示例（curl 仅保留一个只读英文调试样例）。目的：从根上拦截 LLM 默认选 curl 写中文导致乱码的路径。

### 2026-01-31

- **🚨 中文编码警告**：新增重要提示，禁止使用 curl 直接推送包含中文的内容，会导致乱码问题。必须使用 Python、JavaScript 等编程语言调用 API 确保 UTF-8 编码正确。
- **📁 资源路径修正**：修正全局 assets 目录路径为 `{local_path}/data/assets/`
- **🖼️ 图片处理更新**：完善图片上传和插入到思源笔记的流程文档

## 概述

本仓库包含多个针对思源笔记的 Claude Code Skills，采用**分层设计**：

- **基础层**：提供思源笔记的核心概念和通用知识
- **应用层**：针对特定任务的专用工具
- **格式层**：处理特定格式和语法

## Skills 结构

```
skills/
├── siyuan/                    # 基础层：核心知识库
├── siyuan-article-import/     # 应用层：文章导入
├── siyuan-excalidraw/         # 应用层：图表生成
└── siyuan-markdown/           # 格式层：Markdown 编辑
```

## API 调用约定（所有 skill 共用）

所有思源 API 调用必须通过 `_shared/siyuan_client.py` 提供的 `SiyuanClient`，**不要使用 curl 或手写 `requests.post`**。

### 为什么不能用 curl

shell 转义 + UTF-8 在 `curl -d` 上极易出问题：JSON 内嵌套引号、多行内容、中文字符都会被 shell 重新解释，导致写入思源的内容乱码。`requests.post(..., json=...)` 由库负责 UTF-8 编码，从根上规避。

### 基本用法

```python
from _shared.siyuan_client import SiyuanClient

client = SiyuanClient.from_config(__file__)  # 自动加载 .claude/siyuan.json
rows = client.sql("SELECT id FROM blocks WHERE type='d' LIMIT 5")
client.create_doc_with_md(notebook="20240101...", path="/中文文档", markdown="# 标题\n正文")
```

### 已封装的端点

`sql` · `insert_block` · `append_block` · `update_block` · `get_block_kramdown` · `set_block_attrs` · `get_block_attrs` · `create_doc_with_md` · `remove_doc` · `get_ids_by_hpath` · `get_path_by_id` · `list_notebooks` · `get_file`

未封装端点用通用方法：

```python
client.call("/api/notebook/lsNotebooks")
client.call("/api/block/moveBlock", id="块ID", parentID="新父块ID")
```

### 错误处理

非 0 `code` 抛 `SiyuanAPIError`（携带 `code` / `msg` / `endpoint`），不要静默忽略。

### 依赖

`requests`（任意版本）。若系统未装：

- Debian/Ubuntu：`sudo apt install python3-requests`
- 其它：`pip install requests`

---

## 各 Skill 详解

### 1. siyuan - 基础知识库 🔵

**层级**：基础层

**用途**：提供思源笔记的核心概念、通用 API 调用方法、模板语法、闪卡系统等基础知识。

**使用场景**：
- 询问思源笔记的基本概念（内容块、块引用、嵌入块）
- 需要了解思源 API 的一般用法
- 涉及模板开发、闪卡系统等核心功能

**关键内容**：
- 内容块（Block）概念和操作
- 块引用和嵌入块语法
- API 调用方法和最佳实践
- 模板语法（`.action{}`）
- 闪卡系统

**依赖关系**：其他所有 skills 依赖此 skill 提供的基础知识

---

### 2. siyuan-article-import - 文章导入工具 🟢

**层级**：应用层

**用途**：从网络抓取文章（微信公众号、知乎、掘金、博客等）并导入思源笔记。

**使用场景**：
- 需要导入微信文章
- 保存网页内容到思源
- 抓取网络文章

**核心功能**：
- 自动识别文章来源
- 处理图片下载和上传
- 防止重复导入
- 自动创建"知识储备"笔记本

**触发关键词**："导入文章"、"保存网页"、"抓取内容"

**依赖关系**：依赖 `siyuan` 基础知识

---

### 3. siyuan-excalidraw - 图表生成器 🟢

**层级**：应用层

**用途**：为思源笔记创建流程图、思维导图、架构图等可视化内容。

**使用场景**：
- 需要绘制流程图
- 创建思维导图
- 生成系统架构图
- 数据可视化

**核心功能**：
- 生成 Excalidraw 风格的 SVG 图表
- 自动保存到思源资源目录
- 支持多种图表类型（流程图、思维导图、层级图等）

**触发关键词**："绘图"、"画流程图"、"创建架构图"、"可视化"

**依赖关系**：依赖 `siyuan` 基础知识

---

### 4. siyuan-markdown - Markdown 编辑器 🟡

**层级**：格式层

**用途**：处理思源笔记风味 Markdown（SFMD）的编辑和语法。

**使用场景**：
- 编辑思源 .md 文件
- 使用维基链接和块引用
- 插入图片到文档

**核心功能**：
- 维基链接语法（`[[文档]]`）
- 块引用语法（`((块ID))`）
- 嵌入块和属性查询
- 图片插入脚本

**关键语法**：
- `[[文档名]]` - 维基链接
- `((块ID))` - 块引用
- `{{SQL}}` - SQL 查询嵌入

**依赖关系**：依赖 `siyuan` 基础知识

---

## 层级关系图

```
┌─────────────────────────────────────────┐
│          siyuan (基础知识库)            │
│     核心概念、API、模板、块操作         │
│                 ↓                       │
│    ┌────────────┼────────────┐          │
│    ↓            ↓            ↓          │
│ 应用层       应用层       格式层          │
│ (导入)      (绘图)      (编辑)          │
│ siyuan-     siyuan-     siyuan-         │
│ article-    excalidraw  markdown        │
│ import
└─────────────────────────────────────────┘
```

## 使用指南

### 按任务选择 Skill

| 任务 | 使用 Skill |
|------|-----------|
| 了解思源笔记基本概念 | `siyuan` |
| 导入网络文章 | `siyuan-article-import` |
| 创建图表/流程图 | `siyuan-excalidraw` |
| 编辑 Markdown 文件 | `siyuan-markdown` |
| 调用思源 API | `siyuan` |
| 插入图片到文档 | `siyuan-markdown` |

## 安装

### Claude Code

将 `skills/` 目录复制到 `~/.claude/skills/` 或项目根目录的 `/.claude/skills/`。

### 配置文件

推荐在仓库根目录放置 `.claude/siyuan.json`（也兼容根目录 `siyuan.json`）：

```json
{
    "api_url": "http://127.0.0.1:6806",
    "api_token": "your-api-token",
    "local_path": "/path/to/siyuan",
    "remote_path": {
        "webdav": true,
        "url": "https://your-webdav-server.com",
        "username": "username",
        "password": "password",
        "assets_path": "/assets"
    }
}
```

> 💡 **路径说明**：
> - `local_path` 应指向思源笔记的**工作目录**（包含 `data/`、`conf/` 等目录的根目录）
> - 全局 assets 路径为：`{local_path}/data/assets/`
> - 图片引用语法：`assets/filename.ext`（相对于 data 目录）
> - 如果思源运行在 Docker 中，而 skill/脚本运行在宿主机上，`local_path` 应填写**宿主机可访问的挂载路径**
> - 只有当脚本本身也运行在容器内时，`local_path` 才应填写容器内路径（例如 `/siyuan/workspace/`）
> - 如果不使用 WebDAV，保留 `local_path` 即可；`remote_path` 可以省略，或保留但设置 `webdav: false`
>
> **示例目录结构**：
> ```
> Y:\note\siyuan\              # local_path 指向这里
> ├── data/
> │   ├── assets/              # 全局资源目录
> │   └── {笔记本ID}/
> └── conf/
> ```

### Docker 配置说明

如果你的思源跑在 Docker 容器里，需要先判断这个 skill 是在哪里执行：

- **脚本在宿主机执行**：`local_path` 填宿主机挂载出来的目录，例如 `/Users/you/siyuan-workspace`
- **脚本也在同一个容器内执行**：`local_path` 才填写容器内路径，例如 `/siyuan/workspace`

`remote_path` 只有在需要通过 WebDAV 上传资源时才需要配置；否则可以关闭 `webdav` 或直接不填该段。

### 资源上传模式

当前仓库里的图片/资源处理分成两种模式，不是都通过思源 API 上传二进制文件：

#### 模式一：本地直写模式（推荐）

满足以下条件时启用：

- `local_path` 已配置
- skill/脚本可以访问这个思源工作目录

处理方式：

1. 脚本直接把图片或 SVG 写入 `{local_path}/data/assets/`
2. 文档中使用 `assets/文件名` 这种相对路径引用
3. 再通过思源 API 创建文档或追加块内容

这种模式下，**不需要配置 `remote_path`**。

#### 模式二：WebDAV 模式

适用于以下场景：

- 脚本不能直接访问思源工作目录
- 你希望通过远端存储同步资源

这时需要配置：

```json
{
    "remote_path": {
        "webdav": true,
        "url": "https://your-webdav-server.com",
        "username": "username",
        "password": "password",
        "assets_path": "/assets"
    }
}
```

处理方式：

1. 脚本通过 WebDAV `PUT` 上传资源文件
2. 返回 `assets/文件名` 供文档引用
3. 再通过思源 API 写入文档内容

#### 什么时候需要 `remote_path`

- **需要**：你要走 WebDAV 模式
- **不需要**：你已经配置了 `local_path`，而且脚本能直接访问思源工作目录

#### 什么时候是“通过 API 处理”

当前实现里，思源 API 主要用于：

- 创建笔记本
- 创建文档
- 查询文档
- 追加图片块或其他 Markdown 内容

当前实现里，**图片文件本身**不是通过思源 API 上传的，而是：

- 优先写入本地 `data/assets/`
- 或者通过 WebDAV 上传

## 贡献

欢迎贡献！请遵循 skill-creator 标准创建新 skills。

## 参考资源

- [思源笔记官网](https://b3log.org/siyuan/)
- [思源笔记 API 文档](https://b3log.org/siyuan/zh-Hans/api/)
- [Claude Skills 指南](https://github.com/anthropics/skills)
