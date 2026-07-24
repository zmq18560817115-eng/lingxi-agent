"""F3 版式解析 —— 产出布局树。

【当前：模板版】按需求方选的版式返回对应布局树（services/templates.py）。
这是 D3 视觉识别落地前的轻量替代——零 Key、可选多种版式。
D3 接真识别后：当有参考图时，改由真解析产出同 schema 的布局树覆盖模板。

保留 tests/fixtures/layout_tree_sample.json 作为 D3 的目标产物参照。
"""

from __future__ import annotations

from services.templates import layout_tree


def parse(ref_path: str = "", template: str = "two_col") -> dict:
    # D3 起：if ref_path 有真实参考图 → 视觉识别版式；否则按模板。
    _ = ref_path
    return layout_tree(template)
