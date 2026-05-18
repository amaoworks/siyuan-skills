# 思源笔记 API 交互指南

## API 概述

思源笔记提供了一套 RESTful API，支持与外部系统进行数据交互。

- **默认服务地址**：`http://127.0.0.1:6806`
- **请求方法**：所有 API 使用 POST 方法
- **数据格式**：请求和响应均为 JSON 格式
- **完整文档**：[GitHub 官方文档](https://github.com/siyuan-note/siyuan)

## 认证

如果思源笔记开启了 API Token 认证，需要在请求头中携带 Token：

```bash
curl -X POST http://127.0.0.1:6806/api/xxx \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -d '{"key": "value"}'
```

> 💡 **提示**：API Token 在思源笔记设置 → 关于 → API Token 中获取或设置。

## 常用 API 端点分类

### 内容块操作 `/api/block/*`

| 端点 | 描述 |
|------|------|
| /api/block/getBlockKramdown | 获取块 Kramdown 源码 |
| /api/block/insertBlock | 插入块 |
| /api/block/updateBlock | 更新块 |
| /api/block/deleteBlock | 删除块 |
| /api/block/moveBlock | 移动块 |
| /api/block/appendBlock | 追加块 |
| /api/block/prependBlock | 前置块 |
| /api/block/getChildBlocks | 获取子块 |
| /api/block/transferBlockRef | 转移块引用 |

### 文档树操作 `/api/filetree/*`

| 端点 | 描述 |
|------|------|
| /api/filetree/createDocWithMd | 使用 Markdown 创建文档 |
| /api/filetree/renameDoc | 重命名文档 |
| /api/filetree/removeDoc | 删除文档 |
| /api/filetree/moveDocs | 移动文档 |
| /api/filetree/getHPathByPath | 根据路径获取人类可读路径 |
| /api/filetree/getHPathByID | 根据 ID 获取人类可读路径 |
| /api/filetree/getIDsByHPath | 根据人类可读路径获取文档 IDs |
| /api/filetree/getPathByID | 根据 ID 获取系统路径 |

### 文件操作 `/api/file/*`

| 端点 | 描述 |
|------|------|
| /api/file/getFile | 获取文件内容 |
| /api/file/putFile | 上传/写入文件 |
| /api/file/removeFile | 删除文件 |
| /api/file/renameFile | 重命名文件 |
| /api/file/readDir | 读取目录 |

### SQL 查询 `/api/query/*`

| 端点 | 描述 |
|------|------|
| /api/query/sql | 执行 SQL 查询 |

### 属性操作 `/api/attr/*`

| 端点 | 描述 |
|------|------|
| /api/attr/setBlockAttrs | 设置块属性 |
| /api/attr/getBlockAttrs | 获取块属性 |

## Python 调用示例（推荐用法）

所有 API 调用通过 `_shared.siyuan_client.SiyuanClient`。它内部用 `requests`，UTF-8 编码由库保证；中文 / 嵌套引号 / 多行内容写入思源都不会乱码。

```python
from _shared.siyuan_client import SiyuanClient

client = SiyuanClient.from_config(__file__)  # 自动加载 .claude/siyuan.json
```

### SQL 查询

```python
rows = client.sql("SELECT * FROM blocks WHERE type='d' LIMIT 10")
```

### 插入块

```python
client.insert_block(
    parent_id="父块ID",
    markdown="# 新标题\n\n这是内容",  # 中文安全
)
```

### 设置块属性

```python
client.set_block_attrs(
    block_id="块ID",
    attrs={"custom-priority": "high", "custom-status": "doing"},
)
```

### 根据人类可读路径获取文档 IDs

用于把 wiki 的“参考来源”写成可跳转块引用。`path` 使用人类可读路径，例如 `/raw/出行/日本`；返回 ID 数组，通常取第一个结果再写成 `((文档ID "日本"))`。

```python
ids = client.get_ids_by_hpath(path="/raw/出行/日本", notebook="笔记本ID")
if ids:
    source_ref = f'(({ids[0]} "日本")) - 原始素材'
```

### 根据 ID 获取系统路径

可用于把文档 ID 解析为 `notebook` 和 `.sy` 存储路径，便于 `removeDoc`、`getFile` 或排查文件位置。

```python
info = client.get_path_by_id(block_id="20260514161405-wh4qijh")
```

### 获取文件

```python
data = client.get_file("/data/20210808180117-6v0mkxr/20210808180117-czj9bvb.sy")
```

### 任意未封装端点

```python
client.call("/api/notebook/lsNotebooks")
client.call("/api/block/appendBlock", dataType="markdown", data="# 标题", parentID="父块ID")
```

---

### curl（仅限只读英文端点的临时调试）

仅用于确认端点是否在线之类的轻量调试。**禁止用 curl 推送中文或嵌套引号内容** —— shell 转义会损坏 JSON 导致乱码：

```bash
curl -X POST "http://127.0.0.1:6806/api/notebook/lsNotebooks?token=YOUR_TOKEN"
```

## 响应格式

所有 API 的响应遵循统一格式：

```json
{
  "code": 0,
  "msg": "",
  "data": { ... }
}
```

- `code`: 0 表示成功，非 0 表示错误
- `msg`: 错误信息或提示信息
- `data`: 返回的具体数据

## 重要警告

### 🚨 中文编码警告（非常重要！）

> ⚠️ **禁止使用 curl 直接推送包含中文的内容**！
>
> 使用 curl 命令直接向思源笔记 API 推送中文内容会导致**乱码问题**。
>
> **错误示例**（会产生乱码）：
> ```bash
> curl -X POST "http://127.0.0.1:6806/api/filetree/createDocWithMd" \
>   -H "Authorization: Token YOUR_TOKEN" \
>   -H "Content-Type: application/json" \
>   -d '{"markdown": "这是中文内容"}'
> ```
>
> **正确做法**：使用编程语言（Python、JavaScript 等）调用 API，确保正确的 UTF-8 编码：
>
> **Python 示例**（推荐）：
> ```python
> import requests
>
> response = requests.post(
>     'http://127.0.0.1:6806/api/filetree/createDocWithMd',
>     headers={
>         'Authorization': 'Token YOUR_TOKEN',
>         'Content-Type': 'application/json'
>     },
>     json={
>         'notebook': '笔记本ID',
>         'path': '/文档路径',
>         'markdown': '这是中文内容，编码正常'
>     }
> )
> ```
>
> **Node.js 示例**：
> ```javascript
> const response = await fetch('http://127.0.0.1:6806/api/filetree/createDocWithMd', {
>     method: 'POST',
>     headers: {
>         'Authorization': 'Token YOUR_TOKEN',
>         'Content-Type': 'application/json'
>     },
>     body: JSON.stringify({
>         notebook: '笔记本ID',
>         path: '/文档路径',
>         markdown: '这是中文内容，编码正常'
>     })
> });
> ```

### 文件操作警告

> ⚠️ **警告**：插件或外部扩展如果需要读取或写入 `data` 目录下的文件，**请通过调用内核 API 来实现**，不要自行调用 `fs` 或其他 Node.js API，否则可能导致数据同步时分块丢失，造成云端数据损坏。
>
> 请使用 `/api/file/*` 系列 API（如 `/api/file/getFile`、`/api/file/putFile`）。

## 日记文档属性

思源笔记在创建日记时会自动添加 `custom-dailynote-yyyymmdd` 属性，用于将日记文档与普通文档区分。

如果手动创建日记文档（如使用 `createDocWithMd` API），请手动添加该属性，例如：

```json
{
  "custom-dailynote-20250125": "20250125"
}
```

## 已知注意事项 / 待补充

- `/api/filetree/getIDsByHPath` 的返回值 `data` 是 **ID 数组**，调用方不应假设永远只有一个结果；写来源引用前应检查结果数量，必要时结合 `notebook`、`hpath` 或 SQL 再次确认。
- 本文档当前优先覆盖本 skill 常用接口；`/api/filetree/renameDocByID`、`/api/filetree/removeDocByID`、`/api/filetree/moveDocsByID` 等官方已提供但本文尚未展开的接口，后续补齐时应继续以官网 `API.md` / `API_zh_CN.md` 为准。

## 相关资源

- [思源笔记 GitHub 仓库](https://github.com/siyuan-note/siyuan)
- [完整 API 文档](https://github.com/siyuan-note/siyuan/blob/master/API_zh_CN.md)
- [SQL 查询文档](https://github.com/siyuan-note/siyuan/blob/master/SQL_zh_CN.md)
