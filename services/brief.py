"""F5 说明导出 —— 汇总成可交付说明书。

【联调版】优先用缓存的 spec（F2 复述的产物），并把需求方**确认/改写**的
那版复述作为概述回流进来，保证说明书 = 需求方点头的那份理解。
没有缓存 spec 时兜底现算一次。
"""

from __future__ import annotations

import store
from models import Brief
from services.analyze import analyze


def brief(requirement_id: str) -> Brief:
    data = store.get(requirement_id) or {}
    spec = data.get("spec") or analyze(requirement_id).to_dict()

    # 纠偏回流：需求方改写过就用她那版，否则用复述原文（压平成一行）。
    confirmed = (data.get("confirmed_restate") or "").strip()
    summary = confirmed or " ".join(spec.get("restate", "").split())

    return Brief(
        title=f"视觉说明书 · {data.get('brand') or '未命名需求'}",
        summary=summary,
        tone=spec["tone"]["value"],
        composition=spec["composition"]["value"],
        layout=spec["layout"]["value"],
        key_elements=spec.get("key_elements", []),
        avoid=spec.get("avoid", []),
        reference_note="版式骨架参考上传图，配色按上述色调另做。",
    )
