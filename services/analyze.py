"""F2 理解复述 —— 把需求翻译成结构化 VisualSpec + 人话复述。

【D2 真件】优先走真 LLM（Claude Opus 4.8 + 结构化输出）；任何异常
（缺 API Key / 断网 / 鉴权失败 / 解析失败）自动降级到规则版 rule_fallback。
- generation_mode="model"         → LLM 产出
- generation_mode="rule_fallback" → 规则兜底

接口签名与 D1 假件一致：analyze(requirement_id) -> VisualSpec。
调用方（main.py / brief.py）不感知走了哪条路径。

复述文风采用【版本 C · 结构化口语型】：分「色调/构图/排版/参考」四点，
用"我理解你要——"开头、"需要调整吗？"结尾。若需求方选了别的版本，
只需改本文件的 SYSTEM_PROMPT，接口不变。
"""

from __future__ import annotations

import os
from typing import Literal

import store
from models import Sourced, VisualSpec

MODEL = os.environ.get("LINGXI_MODEL", "claude-opus-4-8")

SYSTEM_PROMPT = """\
你是「灵犀」——一个需求翻译器。需求方（通常不懂设计术语）用大白话描述想要的
视觉效果，你要把它翻译成一份结构化的视觉规格，并用人话复述给她确认。

产出四个结构化字段，每个都要标注来源 source：
- 文字描述：需求方原话里明确说了的
- 用户选项：从她勾选的选项推出的
- 默认推断：她没说、你按常识补的
- 参考图：从参考图里看出来的

字段：
- tone 色调、composition 构图、layout 排版：各是一个 {value, source}
- key_elements：画面必须出现的关键元素（如 标题栏、产品卡、价格条）
- avoid：明确要规避的（如 暗黑风、深色底）
- restate：一段给需求方看的口语化复述，风格严格按下面模板

restate 模板（版本 C · 结构化口语型）：
我理解你要——
· 色调：……
· 构图：……
· 排版：……
· 参考：……（若无参考图则省略此条）
需要调整吗？

要求：说人话，不堆术语；把她没说但你推断的部分讲清楚，让她一眼看出对不对。\
"""


def analyze(requirement_id: str) -> VisualSpec:
    req = store.get(requirement_id) or {}
    try:
        return _analyze_with_model(req)
    except Exception:  # noqa: BLE001 —— 缺 Key/断网/鉴权/解析失败，一律降级
        return _analyze_with_rules(req)


# —— 真 LLM 路径 ——
def _analyze_with_model(req: dict) -> VisualSpec:
    import anthropic
    from pydantic import BaseModel

    SourceKind = Literal["文字描述", "用户选项", "默认推断", "参考图"]

    class SourcedOut(BaseModel):
        value: str
        source: SourceKind

    class VisualSpecOut(BaseModel):
        tone: SourcedOut
        composition: SourcedOut
        layout: SourcedOut
        key_elements: list[str]
        avoid: list[str]
        restate: str

    user_msg = (
        f"品牌/产品：{req.get('brand', '')}\n"
        f"用途：{req.get('goal', '')}\n"
        f"需求方原话：{req.get('description', '')}\n"
        f"明确不想要：{req.get('avoid', '')}\n"
        f"参考图数量：{len(req.get('ref_paths', []))}\n\n"
        "请把它翻译成视觉规格并复述。"
    )

    client = anthropic.Anthropic()  # 读取 ANTHROPIC_API_KEY
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        output_format=VisualSpecOut,
    )
    spec = resp.parsed_output
    return VisualSpec(
        tone=Sourced(value=spec.tone.value, source=spec.tone.source),
        composition=Sourced(value=spec.composition.value, source=spec.composition.source),
        layout=Sourced(value=spec.layout.value, source=spec.layout.source),
        key_elements=spec.key_elements,
        avoid=spec.avoid,
        restate=spec.restate,
        generation_mode="model",
    )


# —— 规则兜底路径（断网 / 无 Key）——
def _analyze_with_rules(req: dict) -> VisualSpec:
    desc = req.get("description", "") or ""
    avoid_raw = req.get("avoid", "") or ""
    brand = req.get("brand", "") or "该产品"

    warm = any(k in desc for k in ("暖", "奶油", "小清新", "清爽"))
    dark_avoid = any(k in (desc + avoid_raw) for k in ("暗黑", "深色", "深底"))

    tone_val = "偏暖的清爽色系，不压深" if warm else "低饱和中性色系，干净不刺眼"
    tone_src: Literal["文字描述", "默认推断"] = "文字描述" if warm else "默认推断"

    import re

    parts = [p.strip() for p in re.split(r"[,，、;；\s]+", avoid_raw) if p.strip()]
    avoid: list[str] = []
    for p in parts:  # 去重、保序
        if p not in avoid:
            avoid.append(p)
    if dark_avoid and not any("暗黑" in a for a in avoid):
        avoid.append("暗黑风")

    return VisualSpec(
        tone=Sourced(value=tone_val, source=tone_src),
        composition=Sourced(value="顶部标题栏，主体居中，四周留白约 10%", source="默认推断"),
        layout=Sourced(value="产品分栏排列，价格条置于卡片底部", source="默认推断"),
        key_elements=["标题栏", "产品卡", "价格条"],
        avoid=avoid or ["高饱和", "杂乱"],
        restate=(
            "我理解你要——\n"
            f"· 色调：{tone_val}\n"
            "· 构图：顶部标题栏，主体居中，四周留白\n"
            "· 排版：产品分栏，价格放卡片底部\n"
            f"（当前离线，用规则草拟；{brand}的细节接入模型后会更贴）\n"
            "需要调整吗？"
        ),
        generation_mode="rule_fallback",
    )
