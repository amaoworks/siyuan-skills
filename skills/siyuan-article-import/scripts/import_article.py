#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信文章导入思源笔记脚本

用法:
    python import_article.py <文章URL> [笔记本名称]

示例:
    python import_article.py "https://mp.weixin.qq.com/s/xxx" "微信文章收藏"
"""

import json
import sys
from pathlib import Path
from datetime import datetime

SKILLS_ROOT = Path(__file__).resolve().parents[2]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _shared.siyuan_client import SiyuanAPIError, SiyuanClient


class SiYuanImporter:
    """思源笔记导入器（基于 SiyuanClient）。"""

    def __init__(self, config_path=None):
        """初始化导入器。

        Args:
            config_path: .json 配置文件路径直读；为 None 时向上查找 siyuan.json。
        """
        if config_path and Path(config_path).is_file():
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.client = SiyuanClient(api_url=cfg['api_url'], api_token=cfg['api_token'])
        else:
            self.client = SiyuanClient.from_config(__file__)

    def create_notebook(self, name):
        """创建笔记本，返回 ID；失败返回 None。"""
        try:
            data = self.client.call('/api/notebook/createNotebook', name=name, icon='')
            return data['notebook']['id'] if data else None
        except SiyuanAPIError as e:
            print(f"ERROR|{e.msg}|")
            return None

    def ensure_notebook_exists(self, name):
        """确保笔记本存在，不存在则创建，返回 ID。"""
        for nb in self.client.list_notebooks():
            if nb.get('name') == name:
                return nb.get('id')
        return self.create_notebook(name)

    def create_document(self, notebook_id, title, content):
        """创建文档；client 负责 UTF-8 编码，含中文/引号/换行均安全。返回 doc_id 或 None。"""
        safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '-')[:50]
        try:
            return self.client.create_doc_with_md(notebook_id, f'/{safe_title}', content)
        except SiyuanAPIError as e:
            print(f"ERROR|{e.msg}|")
            return None

    def verify_document(self, doc_id):
        """验证文档块数量；失败返回 -1。"""
        try:
            rows = self.client.sql(
                f"SELECT COUNT(*) as count FROM blocks WHERE root_id='{doc_id}'"
            )
            return rows[0]['count'] if rows else -1
        except SiyuanAPIError:
            return -1


def format_article_content(title, content, url, author='', cover_image=''):
    """格式化文章内容为标准 Markdown 格式

    Args:
        title: 文章标题
        content: 文章正文内容
        url: 文章链接
        author: 作者（可选）
        cover_image: 封面图片 URL（可选）

    Returns:
        格式化后的 Markdown 内容
    """
    # 构建元信息块
    metadata = []
    if author:
        metadata.append(f"**作者**：{author}")
    metadata.append(f"**来源**：微信公众号")
    metadata.append(f"**原始链接**：{url}")
    metadata.append(f"**导入时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

    markdown = f"# {title}\n\n"

    # 添加封面图（如果有）
    if cover_image and cover_image.startswith('http'):
        markdown += f"![封面图]({cover_image})\n\n"

    # 添加元信息
    markdown += "---\n\n" + "\n".join(metadata) + "\n\n---\n\n"

    # 添加正文内容
    markdown += content

    return markdown


def import_wechat_article(url, notebook_name='知识储备', title='', content='', author='', cover_image=''):
    """导入微信文章到思源笔记

    Args:
        url: 文章 URL
        notebook_name: 目标笔记本名称
        title: 文章标题
        content: 文章内容（Markdown 格式）
        author: 作者
        cover_image: 封面图 URL

    Returns:
        (success, message, doc_id)
    """
    try:
        importer = SiYuanImporter()

        # 确保笔记本存在
        notebook_id = importer.ensure_notebook_exists(notebook_name)
        if not notebook_id:
            return (False, "创建笔记本失败", None)

        # 格式化文章内容
        markdown = format_article_content(
            title=title or "未命名文章",
            content=content,
            url=url,
            author=author,
            cover_image=cover_image
        )

        # 创建文档
        doc_id = importer.create_document(notebook_id, title or "未命名文章", markdown)
        if not doc_id:
            return (False, "创建文档失败", None)

        # 验证文档
        block_count = importer.verify_document(doc_id)
        if block_count > 0:
            return (True, f"文档创建成功，共 {block_count} 个内容块", doc_id)
        else:
            return (False, "文档验证失败", doc_id)

    except Exception as e:
        return (False, f"导入失败: {str(e)}", None)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python import_article.py <文章URL> [笔记本名称]")
        sys.exit(1)

    url = sys.argv[1]
    notebook_name = sys.argv[2] if len(sys.argv) > 2 else "知识储备"

    # 注意：实际使用时，需要先使用 web-reader 工具获取文章内容
    # 这里只是示例框架
    print(f"ERROR|需要先使用 web-reader 获取文章内容|")
    print(f"INFO|URL: {url}|")
    print(f"INFO|目标笔记本: {notebook_name}|")


if __name__ == '__main__':
    main()
