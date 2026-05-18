"""端到端 smoke test：验证思源 API 中文写入不乱码。

不依赖 requests（使用标准库 urllib），便于在最小环境下验证。
这是对 SiyuanClient 设计假设的独立验证 —— 都用 JSON+UTF-8 推送 payload，
client.py 在 requests 装好后行为应一致。

流程：
  1. list_notebooks 找一个可用笔记本
  2. createDocWithMd 写一个含中文标题/正文/引号/换行的文档
  3. SQL 查询读回，检查每个特征字符串完整无乱码
  4. removeDoc 清理

退出码 0 = 通过；非 0 = 失败（输出最后一个错误）。
"""

import json
import sys
import time
from pathlib import Path
from urllib import request as urlreq
from urllib.error import HTTPError, URLError

SKILLS_ROOT = Path(__file__).resolve().parents[2]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _shared.siyuan_common import read_config


def api_post(api_url: str, api_token: str, endpoint: str, payload: dict) -> dict:
    """用 urllib 发 JSON POST，模拟 client.call 的行为。"""
    url = f"{api_url.rstrip('/')}{endpoint}?token={api_token}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urlreq.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlreq.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def must_zero(result: dict, endpoint: str) -> dict:
    if result.get("code") != 0:
        raise RuntimeError(f"{endpoint} 失败 code={result.get('code')} msg={result.get('msg')}")
    return result.get("data")


def main() -> int:
    cfg = read_config(__file__)
    api_url, api_token = cfg["api_url"], cfg["api_token"]
    print(f"[+] 配置加载: api_url={api_url}")

    # 1. 找一个笔记本
    nb_data = must_zero(api_post(api_url, api_token, "/api/notebook/lsNotebooks", {}), "lsNotebooks")
    notebooks = nb_data.get("notebooks", []) if isinstance(nb_data, dict) else []
    notebooks = [n for n in notebooks if not n.get("closed")]
    if not notebooks:
        print("[!] 未找到开启状态的笔记本，跳过写入测试。")
        return 1
    nb_id, nb_name = notebooks[0]["id"], notebooks[0]["name"]
    print(f"[+] 使用笔记本: {nb_name} ({nb_id})")

    # 2. 构造一段"恶意" payload —— 中文 + 嵌套引号 + 换行 + emoji + 反斜杠
    #    这正是 curl -d 最容易翻车的内容
    ts = time.strftime("%Y%m%d-%H%M%S")
    doc_title = f"smoke-中文-{ts}"
    doc_path = f"/{doc_title}"
    markers = [
        "中文标题正文",
        '他说"你好世界"',           # 嵌套双引号
        "第一行\n第二行",            # 换行
        "路径 C:\\Users\\test",      # 反斜杠
        "🎉 emoji 也要保住",          # 非 BMP 字符
        "单引号'与混合\"引号",        # 单引号+双引号混合
    ]
    markdown = "# " + doc_title + "\n\n" + "\n\n".join(markers)

    doc_id = must_zero(
        api_post(api_url, api_token, "/api/filetree/createDocWithMd",
                 {"notebook": nb_id, "path": doc_path, "markdown": markdown}),
        "createDocWithMd",
    )
    print(f"[+] 文档已创建: id={doc_id}")

    try:
        # 3. 读回，验证每个 marker 完整
        sql = f"SELECT id, content, markdown FROM blocks WHERE root_id='{doc_id}'"
        rows = must_zero(api_post(api_url, api_token, "/api/query/sql", {"stmt": sql}), "query/sql") or []
        haystack = "\n".join((r.get("markdown") or "") + "\n" + (r.get("content") or "") for r in rows)
        missing = [m for m in markers if m.split("\n")[0] not in haystack]
        if missing:
            print(f"[FAIL] 以下 marker 未在读回内容中找到（疑似乱码）:")
            for m in missing:
                print(f"       - {m!r}")
            print(f"[debug] 读回内容前 500 字: {haystack[:500]!r}")
            return 2
        print(f"[+] 读回 {len(rows)} 个块，所有 marker 完整无乱码 ✓")
        print(f"[+] 验证特征：嵌套引号 / 换行 / 反斜杠 / emoji / 引号混合 全部正常")

    finally:
        # 4. 清理 —— 用 SQL 查到系统路径再 removeDoc
        path_rows = api_post(api_url, api_token, "/api/query/sql",
                             {"stmt": f"SELECT path FROM blocks WHERE id='{doc_id}'"})
        sys_path = ((path_rows.get("data") or [{}])[0] or {}).get("path")
        if sys_path:
            r = api_post(api_url, api_token, "/api/filetree/removeDoc",
                         {"notebook": nb_id, "path": sys_path})
            if r.get("code") == 0:
                print(f"[+] 清理完成: {sys_path}")
            else:
                print(f"[!] 清理失败 code={r.get('code')} msg={r.get('msg')} path={sys_path}")
        else:
            print(f"[!] 未找到 {doc_id} 的系统路径，请手动删除文档 {doc_path}")

    print("\n[PASS] 端到端中文写入测试通过。SiyuanClient 的核心假设（JSON+UTF-8 不乱码）成立。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (HTTPError, URLError) as e:
        print(f"[FAIL] 网络/HTTP 错误: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        sys.exit(4)
