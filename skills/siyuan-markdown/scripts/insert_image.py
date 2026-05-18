#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
思源笔记图片插入脚本

功能：
1. 在指定文档中插入图片
2. 支持本地 assets 路径和 URL 链接两种方式
3. 自动查找文档（通过标题匹配）

使用方法：
    # 插入本地 assets 图片
    python insert_image.py <doc_title> <image_path> [caption]

    # 插入 URL 图片
    python insert_image.py <doc_title> <url> [caption] --url

示例：
    # 本地图片
    python insert_image.py "我的笔记" "assets/diagram.svg" "流程图"

    # URL 图片
    python insert_image.py "我的笔记" "https://example.com/image.png" "网络图片" --url
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _shared.siyuan_client import SiyuanClient


def find_doc_by_title(client, title):
    """通过标题（模糊匹配）查找文档，返回 doc_id。"""
    blocks = client.sql(
        f"SELECT * FROM blocks WHERE content LIKE '%{title}%' AND type = 'd'"
    )
    if not blocks:
        raise Exception(f"Document not found: {title}")
    for block in blocks:
        if title in block.get("content", ""):
            return block.get("id")
    raise Exception(f"Document not found: {title}")


def append_image_to_doc(client, doc_id, image_path, caption, is_url=False):
    """在文档末尾追加图片块。client 负责 UTF-8 编码，caption 含中文无乱码风险。"""
    if caption:
        image_markdown = f'![{caption}]({image_path} "{caption}")'
    else:
        image_markdown = f"![]({image_path})"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"\n{image_markdown}\n\n*Inserted at {timestamp}*\n"
    return client.append_block(parent_id=doc_id, markdown=content)


def print_usage():
    """打印使用说明"""
    print("思源笔记图片插入脚本")
    print("=" * 50)
    print()
    print("使用方法:")
    print(f"  {sys.argv[0]} <doc_title> <image_path> [caption] [--url]")
    print()
    print("参数:")
    print("  doc_title   - 目标文档标题（支持部分匹配）")
    print("  image_path  - 图片路径")
    print("                 本地: assets/image.svg")
    print("                 URL:  https://example.com/image.png")
    print("  caption     - 图片说明文字（可选）")
    print("  --url       - 标识 image_path 为 URL（可选）")
    print()
    print("示例:")
    print(f"  {sys.argv[0]} \"我的笔记\" \"assets/diagram.svg\" \"流程图\"")
    print(f"  {sys.argv[0]} \"我的笔记\" \"https://example.com/image.png\" \"网络图片\" --url")
    print()
    print("返回格式:")
    print("  成功: SUCCESS|块ID|消息")
    print("  失败: ERROR|错误消息")
    print()


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    # 解析参数
    doc_title = sys.argv[1]
    image_path = sys.argv[2]
    caption = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3] == "--url" else ""
    is_url = "--url" in sys.argv

    # 如果 --url 在 caption 位置
    if len(sys.argv) > 3 and sys.argv[3] == "--url":
        caption = sys.argv[4] if len(sys.argv) > 4 else ""

    try:
        client = SiyuanClient.from_config(__file__)
        doc_id = find_doc_by_title(client, doc_title)
        block_id = append_image_to_doc(client, doc_id, image_path, caption, is_url)
        print(f"SUCCESS|{block_id}|Image inserted successfully")

    except Exception as e:
        # 输出错误信息
        print(f"ERROR|{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
