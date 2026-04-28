import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"


def load_module(relative_path: str, module_name: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SiYuanConfigAndAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.config_payload = {
            "api_url": "http://127.0.0.1:6806",
            "api_token": "token",
            "local_path": "/tmp/siyuan-workspace",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_dot_claude_config(self):
        config_dir = self.workspace / ".claude"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "siyuan.json"
        config_file.write_text(
            json.dumps(self.config_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return config_file

    def prepare_fake_script_path(self, relative_script_path: str) -> Path:
        fake_path = self.workspace / relative_script_path
        fake_path.parent.mkdir(parents=True, exist_ok=True)
        return fake_path

    def test_upload_image_reads_dot_claude_config(self):
        self.write_dot_claude_config()
        module = load_module(
            "skills/siyuan-article-import/scripts/upload_image.py",
            "upload_image_module",
        )
        original_file = module.__file__
        module.__file__ = str(
            self.prepare_fake_script_path(
                "skills/siyuan-article-import/scripts/upload_image.py"
            )
        )
        try:
            config = module.read_config()
        finally:
            module.__file__ = original_file
        self.assertEqual(config["api_url"], self.config_payload["api_url"])

    def test_import_article_reads_dot_claude_config(self):
        self.write_dot_claude_config()
        module = load_module(
            "skills/siyuan-article-import/scripts/import_article.py",
            "import_article_module",
        )
        importer = module.SiYuanImporter.__new__(module.SiYuanImporter)
        original_file = module.__file__
        module.__file__ = str(
            self.prepare_fake_script_path(
                "skills/siyuan-article-import/scripts/import_article.py"
            )
        )
        try:
            config = importer._load_config()
        finally:
            module.__file__ = original_file
        self.assertEqual(config["api_token"], self.config_payload["api_token"])

    def test_insert_image_reads_dot_claude_config(self):
        self.write_dot_claude_config()
        module = load_module(
            "skills/siyuan-markdown/scripts/insert_image.py",
            "insert_image_module",
        )
        original_file = module.__file__
        module.__file__ = str(
            self.prepare_fake_script_path(
                "skills/siyuan-markdown/scripts/insert_image.py"
            )
        )
        try:
            config = module.read_config()
        finally:
            module.__file__ = original_file
        self.assertEqual(config["local_path"], self.config_payload["local_path"])

    def test_upload_image_saves_into_data_assets(self):
        module = load_module(
            "skills/siyuan-article-import/scripts/upload_image.py",
            "upload_image_module_save_local",
        )
        asset_path = module.save_local(b"image-bytes", str(self.workspace), "demo.png")
        self.assertEqual(asset_path, "assets/demo.png")
        self.assertTrue((self.workspace / "data" / "assets" / "demo.png").exists())

    def test_upload_asset_saves_into_data_assets(self):
        module = load_module(
            "skills/siyuan-excalidraw/scripts/upload_asset.py",
            "upload_asset_module_save_local",
        )
        asset_path = module.save_local("<svg />", str(self.workspace), "diagram.svg")
        self.assertEqual(asset_path, "assets/diagram.svg")
        self.assertTrue((self.workspace / "data" / "assets" / "diagram.svg").exists())

    def test_shared_helper_prefers_dot_claude_config(self):
        root_config = self.workspace / "siyuan.json"
        root_config.write_text('{"api_url":"http://wrong"}', encoding="utf-8")
        dot_claude_config = self.write_dot_claude_config()

        sys_path_added = False
        if str(SKILLS_ROOT) not in sys.path:
            sys.path.insert(0, str(SKILLS_ROOT))
            sys_path_added = True
        try:
            from _shared.siyuan_common import find_config_file, read_config  # type: ignore

            found = find_config_file(
                self.prepare_fake_script_path("skills/siyuan-markdown/scripts/insert_image.py")
            )
            self.assertEqual(found.resolve(), dot_claude_config.resolve())
            config = read_config(
                self.prepare_fake_script_path("skills/siyuan-markdown/scripts/insert_image.py")
            )
            self.assertEqual(config["api_url"], self.config_payload["api_url"])
        finally:
            if sys_path_added:
                sys.path.remove(str(SKILLS_ROOT))

    def test_shared_helper_resolves_assets_dir(self):
        sys_path_added = False
        if str(SKILLS_ROOT) not in sys.path:
            sys.path.insert(0, str(SKILLS_ROOT))
            sys_path_added = True
        try:
            from _shared.siyuan_common import resolve_assets_dir  # type: ignore

            assets_dir = resolve_assets_dir(str(self.workspace))
            self.assertEqual(assets_dir, self.workspace / "data" / "assets")
        finally:
            if sys_path_added:
                sys.path.remove(str(SKILLS_ROOT))


if __name__ == "__main__":
    unittest.main()
