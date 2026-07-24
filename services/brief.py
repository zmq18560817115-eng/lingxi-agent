"""F5 说明导出 —— 汇总成可交付说明书。

【D1 假件】返回固定内容。D5 替换：由确认后的 VisualSpec + 布局树装配真实 Brief。
格式固定，风险低，因此功能先行。
"""

from __future__ import annotations

import store
from models import Brief
from services.analyze import analyze


def brief(requirement_id: str) -> Brief:
    # D5 起：读确认后的 VisualSpec，组装完整说明书。
    # D1 复用 analyze() 假件的字段，拼一份固定 Brief。
    spec = analyze(requirement_id)
    data = store.get(requirement_id) or {}
    return Brief(
        title=f"视觉说明书 · {data.get('brand', '未命名需求')}",
        summary="偏暖清爽的专业评测封面，顶部标题栏 + 6 款产品双栏分组对照。",
        tone=spec.tone.value,
        composition=spec.composition.value,
        layout=spec.layout.value,
        key_elements=spec.key_elements,
        avoid=spec.avoid,
        reference_note="借用参考图的版式骨架，配色另做（D1 假数据）。",
    )
