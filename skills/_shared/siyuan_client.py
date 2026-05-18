"""思源 API 客户端。

所有 API 调用都应走这里，不要直接用 curl。
shell 转义 + UTF-8 在 `curl -d` 上极易导致中文乱码 / JSON 损坏；
`requests.post(..., json=...)` 由库负责编码，从根上规避。
"""

from pathlib import Path
from typing import Any, Union

import requests

from .siyuan_common import read_config

PathLike = Union[str, Path]


class SiyuanAPIError(RuntimeError):
    def __init__(self, code: int, msg: str, endpoint: str):
        super().__init__(f"{endpoint} failed (code={code}): {msg}")
        self.code = code
        self.msg = msg
        self.endpoint = endpoint


class SiyuanClient:
    """思源 API 极简封装。一个实例对应一份配置。

    用法:
        client = SiyuanClient.from_config(__file__)
        rows = client.sql("SELECT id FROM blocks WHERE type='d' LIMIT 5")
        client.create_doc_with_md(notebook_id, "/我的文档", "# 中文标题\\n正文")
    """

    def __init__(self, api_url: str, api_token: str, timeout: float = 30.0):
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._session = requests.Session()

    @classmethod
    def from_config(cls, start_path: PathLike) -> "SiyuanClient":
        cfg = read_config(start_path)
        return cls(api_url=cfg["api_url"], api_token=cfg["api_token"])

    def call(self, endpoint: str, **payload: Any) -> Any:
        """调用任意端点。返回 data 字段；非 0 code 抛 SiyuanAPIError。

        endpoint 形如 "/api/block/insertBlock"。
        """
        url = f"{self.api_url}{endpoint}?token={self.api_token}"
        resp = self._session.post(
            url,
            json=payload or {},
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") != 0:
            raise SiyuanAPIError(result.get("code", -1), result.get("msg", ""), endpoint)
        return result.get("data")

    # ---------- 查询 ----------

    def sql(self, stmt: str) -> list:
        return self.call("/api/query/sql", stmt=stmt) or []

    # ---------- 块操作 ----------

    def insert_block(self, parent_id: str, markdown: str, previous_id: str = "") -> Any:
        return self.call(
            "/api/block/insertBlock",
            dataType="markdown",
            data=markdown,
            parentID=parent_id,
            previousID=previous_id,
        )

    def append_block(self, parent_id: str, markdown: str) -> Any:
        return self.call(
            "/api/block/appendBlock",
            dataType="markdown",
            data=markdown,
            parentID=parent_id,
        )

    def update_block(self, block_id: str, markdown: str) -> Any:
        return self.call(
            "/api/block/updateBlock",
            dataType="markdown",
            data=markdown,
            id=block_id,
        )

    def get_block_kramdown(self, block_id: str) -> Any:
        return self.call("/api/block/getBlockKramdown", id=block_id)

    # ---------- 属性 ----------

    def set_block_attrs(self, block_id: str, attrs: dict) -> Any:
        return self.call("/api/attr/setBlockAttrs", id=block_id, attrs=attrs)

    def get_block_attrs(self, block_id: str) -> dict:
        return self.call("/api/attr/getBlockAttrs", id=block_id) or {}

    # ---------- 文档树 ----------

    def create_doc_with_md(self, notebook: str, path: str, markdown: str) -> str:
        return self.call(
            "/api/filetree/createDocWithMd",
            notebook=notebook,
            path=path,
            markdown=markdown,
        )

    def remove_doc(self, notebook: str, path: str) -> Any:
        """path 必须是系统路径（如 /xxxxx.sy），不是人类可读路径。"""
        return self.call("/api/filetree/removeDoc", notebook=notebook, path=path)

    def get_ids_by_hpath(self, path: str, notebook: str) -> list:
        """根据人类可读路径解析文档 ID 列表（数组，可能为空或多元素）。"""
        return self.call("/api/filetree/getIDsByHPath", path=path, notebook=notebook) or []

    def get_path_by_id(self, block_id: str) -> Any:
        return self.call("/api/filetree/getPathByID", id=block_id)

    # ---------- 笔记本 ----------

    def list_notebooks(self) -> list:
        data = self.call("/api/notebook/lsNotebooks") or {}
        return data.get("notebooks", []) if isinstance(data, dict) else []

    # ---------- 文件 ----------

    def get_file(self, path: str) -> bytes:
        """获取 data 目录下文件的原始字节（非 JSON 响应）。"""
        url = f"{self.api_url}/api/file/getFile?token={self.api_token}"
        resp = self._session.post(url, json={"path": path}, timeout=self.timeout)
        resp.raise_for_status()
        return resp.content
