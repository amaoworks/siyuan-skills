---
name: siyuan
description: 思源笔记基础知识库，提供核心概念（内容块、块引用、嵌入块）、通用 API 调用方法、模板语法、闪卡系统等基础知识。当询问思源笔记的基本概念、API 原理、块操作语法、模板开发或通用操作时使用此技能（基础层，不包含特定任务的实现）。
license: Complete terms in LICENSE.txt
---

# 思源笔记技能指南

思源笔记是一款基于内容块的隐私优先知识管理工具。本技能提供了思源笔记的核心操作指南，涵盖内容块管理、模板开发、API交互和闪卡系统等功能模块。

## ⚠️ 调用 API 的硬约束（先看这里）

**所有 API 调用必须用 Python，不要用 curl。** 使用 `_shared/siyuan_client.py` 提供的 `SiyuanClient`，常用端点已封装；UTF-8 编码由 `requests` 库保证，中文 / 嵌套引号 / 多行内容写入思源不会乱码。

curl 仅限只读、纯英文端点的临时调试。**禁止用 curl 写入中文或多行内容** —— shell 转义会损坏 JSON，写进思源的内容会乱码。

> **依赖**：`requests`（Python ≥ 3.7）。未安装时：`sudo apt install python3-requests`（Debian/Ubuntu）或 `pip install requests`。

```python
from _shared.siyuan_client import SiyuanClient

client = SiyuanClient.from_config(__file__)  # 自动加载 .claude/siyuan.json
client.create_doc_with_md(notebook="20240101...", path="/我的文档", markdown="# 中文标题\n正文")
```

完整 API 用法见 [api.md](references/api.md)。

## 核心概念

- **内容块（Block）**：思源笔记的基本单位，每个块通过全局唯一 ID 标识。ID 由时间戳和 7 位随机字符组成，形如 `202008250000-a1b2c3d`。
- **默认 API 端口**：`http://127.0.0.1:6806`
- **数据存储**：SQLite 数据库，主表为 `blocks`

## 功能模块

| 模块 | 描述 | 参考文档 |
|------|------|----------|
| 内容块操作 | 内容块的创建、查询、修改和删除，以及块引用和嵌入块的使用 | [block.md](references/block.md) |
| 模板开发 | 模板片段的创建和使用，支持动态内容生成和变量替换 | [template.md](references/template.md) |
| API 交互 | 思源笔记 API 的调用方法，包括 RESTful 接口和 WebSocket | [api.md](references/api.md) |
| 闪卡系统 | 间隔重复记忆系统的使用，卡片创建、复习和管理 | [flashcard.md](references/flashcard.md) |

## 快速参考

### 块类型代码（用于 SQL 查询）

| 代码 | 类型 |
|------|------|
| `d` | 文档块 |
| `h` | 标题块 |
| `l` | 列表块（包含有序/无序/任务） |
| `i` | 列表项块 |
| `b` | 引述块 |
| `callout` | 提示块 |
| `s` | 超级块 |
| `p` | 段落块 |
| `c` | 代码块 |
| `m` | 公式块 |
| `t` | 表格块 |
| `av` | 数据库块 |
| `query_embed` | 嵌入块 |

#### 子类型（subtype）

- **列表块/列表项块**：`o`（有序）、`u`（无序）、`t`（任务）
- **标题块**：`h1`~`h6`

### 常用语法

#### 块引用
```markdown
((块ID "锚文本"))
((块ID))
```

#### 嵌入块
```markdown
{{SELECT * FROM blocks WHERE content LIKE '%关键词%'}}
```

#### API 调用
```http
POST http://127.0.0.1:6806/api/xxx
Content-Type: application/json

{
  "key": "value"
}
```

### API 示例

```python
from _shared.siyuan_client import SiyuanClient
client = SiyuanClient.from_config(__file__)

client.get_block_kramdown("202008250000-a1b2c3d")
client.sql("SELECT * FROM blocks WHERE type='d'")
```

### 模板示例

**注意**：思源笔记模板使用 `.action{action}` 语法（而非 `{{action}}`）来避免语法冲突。

#### 简单日期模板
```markdown
今天是 `.action{ now | date "2006-01-02" }`。

# `.action{ .title }`

文档ID：`.action{ .id }`
```

#### 查询块模板
```template
.action{ $blocks := queryBlocks "SELECT * FROM blocks WHERE content LIKE '?' LIMIT ?" "%关键词%" "5" }
.action{ range $blocks }
- ((`.action{ .id }`))
.action{ end }
```

#### 带条件的模板
```template
.action{ $before := (div (now.Sub (toDate "2006-01-02" "2020-02-19")).Hours 24) }
距离 2020-02-19 已经过去 `.action{ $before }` 天
```

## 经验教训与最佳实践

### API 调用注意事项

#### 1. 调用副作用与输出是分离的

脚本在 print/log 时崩溃不会回滚 API 已经成功的副作用（如已创建的文档）。重要操作前先用 SQL 检查是否已存在，不要把"没看到成功输出"当成"操作没发生"。

#### 2. 文档路径的三种形式

- **系统路径**：`/20260125135312-pkzku0u.sy` —— 用于 `client.remove_doc`
- **人类可读路径（hpath）**：`/测试文档-20260125-135311` —— 用于显示和 `client.get_ids_by_hpath`
- **文档块 ID**：`20260125135312-pkzku0u` —— 用于块引用 `((doc_id "锚文本"))`

```python
# 从 doc_id 查系统路径（删除文档时需要）
info = client.get_path_by_id(doc_id)
client.remove_doc(notebook_id, info["path"])     # 注意必须用 .sy 系统路径

# 从 hpath 反查 doc_id（写来源引用时需要真实块 ID，不是 [[文档名]]）
ids = client.get_ids_by_hpath(path="/raw/出行/日本", notebook=notebook_id)
if ids:
    source_ref = f'(({ids[0]} "日本")) - 原始素材'
```

> `getIDsByHPath` 返回数组，应检查长度。`[[文档名]]` 仅适合一般双链，**不适合作为可验证的来源引用**。

#### 3. 避免重复操作

脚本崩溃或重复运行容易创建重复文档。创建前用 SQL 检查：

```python
def ensure_doc_exists(client, notebook_id, hpath, markdown):
    rows = client.sql(
        f"SELECT id FROM blocks WHERE box='{notebook_id}' AND hpath='{hpath}' AND type='d'"
    )
    if rows:
        return rows[0]["id"]
    return client.create_doc_with_md(notebook_id, hpath, markdown)
```

### Markdown 图片格式规范

**重要：思源笔记中的图片必须使用标准 Markdown 格式 `![alt](url)`**

#### 正确格式 ✅
```markdown
![图片说明](https://example.com/image.jpg)
![封面图](https://mmbiz.qpic.cn/xxx/0?wx_fmt=jpeg)
![本地图片](assets/image.png)
```

#### 错误格式 ❌
```markdown
!图片 https://example.com/image.jpg
图片：https://example.com/image.jpg
<img src="https://example.com/image.jpg">
```

#### 图片 URL 类型

| 类型 | 示例 | 说明 |
|-----|------|------|
| **网络图片** | `https://example.com/img.jpg` | 直接使用 URL，无需下载 |
| **微信图片** | `https://mmbiz.qpic.cn/...` | 使用原始 URL |
| **本地图片** | `assets/image.png` | 相对于文档的本地路径 |

**注意：不要下载图片后上传，直接使用原始 URL 链接即可。**

#### 修复错误格式的图片

如果图片格式错误，使用以下方法修复：

```python
# 1. 查询包含图片的块
query = f"SELECT id, content FROM blocks WHERE content LIKE '%http%' AND type='p'"
result = api.query_sql(query)

# 2. 找到格式错误的图片并修复
for block in result:
    content = block['content']
    if 'mmbiz.qpic.cn' in content or 'example.com' in content:
        # 提取URL（假设格式为 "文本 URL"）
        url = content.split()[-1] if ' ' in content else content
        # 转换为标准格式
        new_content = f'![图片]({url})'
        # 更新块
        api.update_block(block['id'], new_content)
```

### 测试与调试

#### 推荐的测试流程
1. **先测试连接**：列出笔记本验证 API 连接
2. **使用测试笔记本**：在专门的测试笔记本中操作
3. **创建临时文档**：使用带时间戳的文档名
4. **验证结果**：查询数据库确认操作成功
5. **清理测试数据**：测试完成后删除临时文档

#### 调试技巧
```python
# 1. 保存 API 响应到文件以便检查
with open('debug_response.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 2. 使用 SQL 查询验证数据状态
query = "SELECT * FROM blocks WHERE id = 'xxx' ORDER BY created DESC LIMIT 5"

# 3. 记录操作日志
import logging
logging.basicConfig(filename='siyuan_api.log', level=logging.DEBUG)
```
