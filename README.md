# 思源笔记 Skills Collection

思源笔记（SiYuan Note）技能集合，采用分层设计提供基础知识和专用工具。

这些 skills 遵循 [Claude Skills 规范](https://github.com/anthropics/skills)，可被 Claude Code 和其他兼容 agent 使用。

## ⚠️ 重要更新

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

确保 `.claude/siyuan.json` 包含：

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
>
> **示例目录结构**：
> ```
> Y:\note\siyuan\              # local_path 指向这里
> ├── data/
> │   ├── assets/              # 全局资源目录
> │   └── {笔记本ID}/
> └── conf/
> ```

## 贡献

欢迎贡献！请遵循 skill-creator 标准创建新 skills。

## 参考资源

- [思源笔记官网](https://b3log.org/siyuan/)
- [思源笔记 API 文档](https://b3log.org/siyuan/zh-Hans/api/)
- [Claude Skills 指南](https://github.com/anthropics/skills)
