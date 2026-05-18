# 思源笔记 API 参考（article-import 视角）

文章导入 skill 的所有 API 调用都通过 `_shared.siyuan_client.SiyuanClient`。本文只覆盖 article-import 用到的核心场景；通用 SiyuanClient 用法见 [siyuan/references/api.md](../../siyuan/references/api.md)。

## 配置加载

```python
from _shared.siyuan_client import SiyuanAPIError, SiyuanClient

client = SiyuanClient.from_config(__file__)
```

`from_config` 沿目录向上查找 `.claude/siyuan.json` 或 `siyuan.json`，自动注入 `api_url` / `api_token`。无需自行 `json.load`、无需手写 token。

## 核心场景

### 1. 确保"知识储备"笔记本存在

```python
def ensure_notebook(name):
    for nb in client.list_notebooks():
        if nb.get('name') == name:
            return nb['id']
    data = client.call('/api/notebook/createNotebook', name=name, icon='')
    return data['notebook']['id']
```

> 端点是 `createNotebook`（小写 b），不是 `createNoteBook`。列表端点是 `lsNotebooks`，不是 `listNotebooks`。这两个名字在不少外部资料里被抄错。

### 2. 检查文档是否已存在

```python
def find_existing_doc(notebook_id, title):
    safe_title = title.replace("'", "''")  # SQL 引号转义
    rows = client.sql(
        f"SELECT id FROM blocks "
        f"WHERE type = 'd' AND content = '{safe_title}' AND box = '{notebook_id}' "
        f"LIMIT 1"
    )
    return rows[0]['id'] if rows else None
```

`client.sql(...)` 返回 dict 列表（`[{"id":"..."}]`），用 `rows[0]['id']` 而不是 `rows[0][0]`。

### 3. 创建文档

```python
def create_doc(notebook_id, title, markdown):
    safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '-')[:50]
    try:
        return client.create_doc_with_md(notebook_id, f'/{safe_title}', markdown)
    except SiyuanAPIError as e:
        print(f"ERROR|{e.msg}|")
        return None
```

`create_doc_with_md` 返回新文档的根块 ID 字符串。客户端用 `requests` 库的 JSON 编码，中文 / 嵌套引号 / 多行内容均安全。

### 4. 验证文档创建成功

API 返回大响应偶尔会断开。创建后立刻 SQL 查一次确认：

```python
def verify_doc(doc_id):
    rows = client.sql(f"SELECT COUNT(*) AS n FROM blocks WHERE root_id='{doc_id}'")
    return rows[0]['n'] if rows else 0
```

## 响应格式

所有 `client.*` 方法已经把 `code != 0` 抛成 `SiyuanAPIError`，调用方不需要自己解析 `code` / `msg`。

未封装的端点用 `client.call('/api/...', **payload)`，行为一致：

```python
client.call('/api/notification/pushMsg', msg='导入完成', timeout=3000)
```

## 相关资源

- [思源笔记 API 文档（中文）](https://github.com/siyuan-note/siyuan/blob/master/API_zh_CN.md)
- [思源笔记 API 文档（英文）](https://github.com/siyuan-note/siyuan/blob/master/API.md)
- [SiyuanClient 通用用法](../../siyuan/references/api.md)
