"""F3 版式解析 —— 从参考图识别版式结构，产出布局树。

【D1 假件】直接读手写的 fixtures/layout_tree_sample.json。
该 JSON 同时是 D3 真实解析的"目标产物参照"——真件必须产出同结构。
D3 替换：接真解析（视觉模型 / 规则），返回同 schema 的 dict。
"""

from __future__ import annotations

import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "layout_tree_sample.json"


def parse(ref_path: str) -> dict:
    # D3 起：读取 ref_path 指向的参考图 → 识别标题栏 / N×M 网格 → 产出布局树。
    # D1 忽略 ref_path，返回手写目标产物。
    _ = ref_path
    return json.loads(FIXTURE.read_text(encoding="utf-8"))
