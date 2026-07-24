"""F2 理解复述 —— 把需求翻译成结构化 VisualSpec + 人话复述。

【D1 假件】当前返回硬编码结果，签名与真实版完全一致。
D2 替换内部实现：接真 LLM，断网时 generation_mode 落为 'rule_fallback'。
调用方（main.py / brief.py）不感知这次替换。
"""

from __future__ import annotations

import store
from models import Sourced, VisualSpec


def analyze(requirement_id: str) -> VisualSpec:
    # D2 起：读取 store.get(requirement_id) 的原始需求 → 调 LLM → 产出 VisualSpec。
    # D1 先返回吸奶器评测封面案例的假数据，让全链路能走通。
    _ = store.get(requirement_id)  # 占位：证明假件已能拿到需求上下文
    return VisualSpec(
        tone=Sourced(value="偏暖的清爽色系，主色 #F5B841，底色 #FFF9EF，不压深", source="文字描述"),
        composition=Sourced(value="顶部标题栏，下方左右分组对照，四周留白约 10%", source="用户选项"),
        layout=Sourced(value="6 款产品分两栏，每栏 3 个，价格条置于卡片底部", source="默认推断"),
        key_elements=["标题栏", "分组头", "产品卡", "价格条"],
        avoid=["暗黑风", "深色底"],
        restate=(
            "我理解你要——偏暖的清爽评测风，画面别塞满、四周留空。"
            "上面是标题条，下面把 6 款分成活塞泵和隔膜泵左右对照，每款配价格。"
            "会避开暗黑风和深底色。参考图我主要借它的版式骨架，配色不跟。对吗？"
            "（D1 假数据）"
        ),
        generation_mode="model",
    )
