"""D1 端到端骨架冒烟测试：填表 → 复述 → 确认 → 出图 → 导出，全链路走通。

用 FastAPI TestClient，不起真实服务器。
运行：python -m pytest tests/ -q   或   python tests/test_skeleton.py
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("LINGXI_DATA_DIR", tempfile.mkdtemp(prefix="lingxi-test-"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


def test_end_to_end_skeleton() -> None:
    client = TestClient(main.app)

    # F1 录入
    r = client.post(
        "/requirements",
        data={"brand": "测试吸奶器", "goal": "评测封面", "description": "清爽暖色", "avoid": "暗黑风"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    rid = r.headers["location"].split("/")[2]

    # F2 复述
    spec = client.get(f"/api/requirements/{rid}/analyze").json()
    assert spec["restate"]
    assert spec["tone"]["source"] in {"文字描述", "用户选项", "默认推断", "参考图", "用户修改"}
    assert spec["generation_mode"] in {"model", "rule_fallback"}

    # 逐字段纠偏：改色调 + 规避，确认后应回流到缓存 spec 且来源标「用户修改」
    c = client.post(
        f"/api/requirements/{rid}/confirm",
        data={"tone": "冷淡的高级灰蓝", "avoid": "暖色、圆角", "confirmed_restate": "就按这个来"},
    ).json()
    assert c["ok"] and c["next"].endswith("/preview")
    edited = client.get(f"/api/requirements/{rid}/analyze").json()
    assert edited["tone"]["value"] == "冷淡的高级灰蓝"
    assert edited["tone"]["source"] == "用户修改"
    assert "暖色" in edited["avoid"] and "圆角" in edited["avoid"]

    # F4 渲染 → 1080×1440 PNG
    rd = client.post(f"/api/requirements/{rid}/render").json()
    assert rd["ok"]
    png = client.get(rd["png"])
    assert png.status_code == 200 and png.headers["content-type"] == "image/png"

    # F5 导出说明
    brief = client.get(f"/api/requirements/{rid}/brief").json()
    assert brief["title"] and brief["tone"] and brief["key_elements"]

    print("端到端骨架 ✓  requirement_id =", rid)


if __name__ == "__main__":
    test_end_to_end_skeleton()
