"""SiyuanClient 真实集成测试。

跑过 smoke_test.py 后再跑这个：smoke_test 用 urllib 证明了底层 HTTP 路径正确，
本测试用 client.py 真实方法跑同样的端到端流程，外加 SiyuanAPIError 行为验证。

退出码：0 = 全部通过；非 0 = 至少一项失败（已打印明细）。
"""

import sys
import time
from pathlib import Path
from typing import List, Tuple

SKILLS_ROOT = Path(__file__).resolve().parents[2]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _shared.siyuan_client import SiyuanAPIError, SiyuanClient


PASSED: List[str] = []
FAILED: List[Tuple[str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  ✓ {name}")
    else:
        FAILED.append((name, detail))
        print(f"  ✗ {name}  -- {detail}")


def main() -> int:
    client = SiyuanClient.from_config(__file__)
    print(f"[+] client 已构造，api_url={client.api_url}")

    # ---- 1. list_notebooks / sql ----
    print("\n[1] list_notebooks / sql")
    notebooks = client.list_notebooks()
    check("list_notebooks 返回非空", len(notebooks) > 0)
    open_nbs = [n for n in notebooks if not n.get("closed")]
    if not open_nbs:
        print("[abort] 无 open 笔记本")
        return 1
    nb_id, nb_name = open_nbs[0]["id"], open_nbs[0]["name"]
    print(f"      使用: {nb_name} ({nb_id})")

    rows = client.sql("SELECT id FROM blocks WHERE type='d' LIMIT 3")
    check("sql() 返回 list", isinstance(rows, list))

    # ---- 2. create_doc_with_md（恶劣 payload）----
    print("\n[2] create_doc_with_md（中文 + 嵌套引号 + 反斜杠 + emoji）")
    ts = time.strftime("%Y%m%d-%H%M%S")
    title = f"client-test-中文-{ts}"
    nasty_md = (
        f"# {title}\n\n"
        '他说"你好世界"，然后写道：\n\n'
        "```\n第一行\n第二行 with \\backslash\n```\n\n"
        "- 单引号'与双引号\"混合\n"
        "- emoji: 🎉🌏✨\n"
    )
    doc_id = client.create_doc_with_md(notebook=nb_id, path=f"/{title}", markdown=nasty_md)
    check("doc_id 是字符串", isinstance(doc_id, str) and len(doc_id) > 10, repr(doc_id))

    # 立即记下系统路径，便于 finally 清理（即使后续测试抛错也能删）
    path_info = client.get_path_by_id(doc_id) if doc_id else None
    sys_path = path_info.get("path") if isinstance(path_info, dict) else None
    print(f"      doc_id={doc_id}  sys_path={sys_path}")

    try:
        # ---- 3. get_block_kramdown ----
        print("\n[3] get_block_kramdown")
        kram = client.get_block_kramdown(doc_id)
        kram_str = (kram or {}).get("kramdown", "") if isinstance(kram, dict) else ""
        check("kramdown 含标题", title in kram_str, f"前 200 字: {kram_str[:200]!r}")

        # ---- 4. SQL 验证 marker 完整 ----
        print("\n[4] sql 验证 marker（中文完整性）")
        blocks = client.sql(f"SELECT id, markdown, content FROM blocks WHERE root_id='{doc_id}'")
        hay = "\n".join((b.get("markdown") or "") + "\n" + (b.get("content") or "") for b in blocks)
        for marker in ['你好世界', '🎉', '\\backslash', "单引号'", '双引号"']:
            check(f"marker {marker!r}", marker in hay, f"hay 前 500: {hay[:500]!r}")

        # ---- 5. set/get_block_attrs（合法 key + 中文 value）----
        print("\n[5] set/get_block_attrs（中文 value）")
        client.set_block_attrs(doc_id, {"custom-test-cn": "中文值-✓-🎉", "custom-priority": "high"})
        attrs = client.get_block_attrs(doc_id)
        check("中文 value 完整无乱码", attrs.get("custom-test-cn") == "中文值-✓-🎉",
              repr(attrs.get("custom-test-cn")))
        check("英文 key 写入", attrs.get("custom-priority") == "high")

        # ---- 6. append_block / update_block ----
        print("\n[6] append_block / update_block")
        append_result = client.append_block(
            parent_id=doc_id, markdown="## 追加段落\n这是追加的中文内容。"
        )
        check("append_block 调用成功", append_result is not None)

        # 从 doOperations 中挖新块 id，避免依赖思源 SQL 索引的异步刷新
        new_block_id = None
        if isinstance(append_result, list) and append_result:
            op0 = append_result[0]
            if isinstance(op0, dict):
                ops = op0.get("doOperations") or []
                if ops and isinstance(ops[0], dict):
                    new_block_id = ops[0].get("id")
        check("从 append 返回值拿到新块 id", bool(new_block_id),
              f"return 前 200: {str(append_result)[:200]}")

        if new_block_id:
            client.update_block(new_block_id, markdown="## 已更新-中文标题")
            # 用 kramdown 直读块状态，不走 SQL 索引（避免异步刷新延迟）
            kram = client.get_block_kramdown(new_block_id)
            kram_text = (kram or {}).get("kramdown", "") if isinstance(kram, dict) else ""
            check("update_block 生效（kramdown 直读）",
                  "已更新" in kram_text, repr(kram_text[:200]))

        # ---- 7. get_ids_by_hpath ----
        print("\n[7] get_ids_by_hpath")
        ids = client.get_ids_by_hpath(path=f"/{title}", notebook=nb_id)
        check("hpath 反查找到 doc_id", doc_id in ids, f"got ids={ids}")

        # ---- 8. get_path_by_id（前面已调用过，这里只校验返回值）----
        print("\n[8] get_path_by_id")
        check("sys_path 以 .sy 结尾", isinstance(sys_path, str) and sys_path.endswith(".sy"),
              repr(sys_path))

        # ---- 9. SiyuanAPIError 验证（中文属性名应被服务端拒绝）----
        print("\n[9] SiyuanAPIError 验证（思源拒绝中文属性 key）")
        try:
            client.set_block_attrs(doc_id, {"中文键": "value"})
            check("非法 key 应抛错", False, "client 未抛错")
        except SiyuanAPIError as e:
            check("捕获到 SiyuanAPIError", True)
            check("endpoint 字段正确", e.endpoint == "/api/attr/setBlockAttrs", repr(e.endpoint))
            check("msg 非空且含错误描述", bool(e.msg) and len(e.msg) > 5, repr(e.msg))
            check("code 非 0", e.code != 0, f"code={e.code}")

        # ---- 10. call() 兜底未封装端点 ----
        print("\n[10] call() 兜底")
        result = client.call("/api/notebook/lsNotebooks")
        check("call() 返回 dict 含 notebooks", isinstance(result, dict) and "notebooks" in result)

    finally:
        # ---- 11. remove_doc 清理 ----
        print("\n[11] remove_doc 清理")
        if sys_path:
            try:
                client.remove_doc(notebook=nb_id, path=sys_path)
                check("remove_doc 未抛错", True)
            except SiyuanAPIError as e:
                check("remove_doc 未抛错", False, str(e))
        else:
            print(f"  ! 缺 sys_path，请手动删除 /{title}")

    # ---- 总结 ----
    print(f"\n{'='*50}")
    print(f"通过 {len(PASSED)} 项 / 失败 {len(FAILED)} 项")
    if FAILED:
        print("\n失败明细：")
        for name, detail in FAILED:
            print(f"  - {name}: {detail}")
        return 2
    print("\n[PASS] SiyuanClient 所有方法验证通过。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[FAIL] 测试中断: {type(e).__name__}: {e}")
        sys.exit(3)
