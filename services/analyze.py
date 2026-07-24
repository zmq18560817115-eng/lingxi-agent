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
视觉效果，你要把它拆解成一份结构化的视觉规格，并用人话复述给她确认。

## 拆解成这些字段
- tone 色调、composition 构图、layout 排版：各是 {value, source}
- key_elements：画面必须出现的关键元素（可命名的块，如 标题栏、产品卡、价格条）
- avoid：明确要规避的（短词，如 暗黑风、深色底）
- restate：给需求方看的一段人话复述（格式见末尾）

## 来源判定规则（严格执行，这是本产品的命门）
每个 {value} 都要标 source。按下面的**决策顺序**判，命中即停：

1. **文字描述** —— 该结论能对应到需求方原话里的**具体词**。
   例：她说"暖色" → 色调标 文字描述；她说"留白" → 构图含"留白"标 文字描述。
2. **用户选项** —— 该结论来自她填的结构化字段（用途 goal、品牌 brand、规避 avoid）。
3. **参考图** —— **只有当参考图数量 > 0**，且该结论确实取自参考图时才可用。
   参考图数量为 0 时，**绝对不许**出现 参考图，违者视为错误。
4. **默认推断** —— 以上都不满足，是你按常识补的。

关键纪律：
- **禁止把推断伪装成明说**。她没提的，一律 默认推断，不许标 文字描述。
- **"说了但不精确"怎么标**：方向来自原话、只是数值/色号是你补的 → 仍标 **文字描述**
  （例："小清新暖色" → value 可写"偏暖低饱和，主色#F5B841"，source=文字描述，
  因为方向是她说的；但把数值控制在稳妥范围，别过度发挥）。
  整条都是你凭空补的（她只字未提）→ 标 **默认推断**。
- 拿不准 文字描述 还是 默认推断 时，**从严选 默认推断**——宁可说"这是我猜的"。

## restate（版本 C · 结构化口语型，必须让她一眼看出哪条是你猜的）
我理解你要——
· 色调：……
· 构图：……
· 排版：……
· 参考：……（参考图数量为 0 时省略此条）
其中【括号里标出你替她定的部分，如"（留白我按 10% 定的）"】。需要调整吗？

说人话、不堆术语；把"她没说但你推断"的部分在复述里显式点出来。

## 示例 1（有明说 + 推断，无参考图）
输入：品牌=某吸奶器评测；用途=6款产品专业评测封面；
原话="专业评测、色调小清新不要太深、适当留白"；不想要="暗黑风、深色底"；参考图数量=0
拆解：
- tone = {value:"偏暖的清爽低饱和色系，主色#F5B841，不压深", source:"文字描述"}
  （"小清新不要太深"是原话方向，色号是我补的稳妥值）
- composition = {value:"顶部标题栏，主体居中，四周留白约10%", source:"文字描述"}
  （"留白"她说了，"10%"是我定的）
- layout = {value:"6款产品分两栏、每栏3个，价格条置于卡片底部", source:"默认推断"}
  （分栏方式她没说，全是我补的）
- key_elements = ["标题栏","分组头","产品卡","价格条"]
- avoid = ["暗黑风","深色底"]
- restate = "我理解你要——\\n· 色调：干净清爽的暖色，不压深\\n· 构图：顶部标题栏、
  主体居中，四周留白（留白我按10%定的）\\n· 排版：6款分两栏对照、每款配价格（分栏是我
  替你定的）\\n会避开暗黑风和深色底。需要调整吗？"

## 示例 2（几乎全靠推断，防止乱标 文字描述/参考图）
输入：品牌=山野手冲咖啡；用途=菜单头图；原话="干净点就行"；不想要=""；参考图数量=0
拆解：
- tone = {value:"低饱和大地色系，米白底配深棕字", source:"默认推断"}
  （"干净"太宽泛，具体配色是我补的 → 默认推断，不许标 文字描述）
- composition = {value:"左文右图或上图下文，留白充足", source:"默认推断"}
- layout = {value:"分类标题 + 条目列表，价格右对齐", source:"默认推断"}
- key_elements = ["品牌名","分类标题","条目行","价格"]
- avoid = []（她没明确说规避什么，就留空，别硬编）
- restate 里要坦白："你只说了'干净'，所以配色和版式基本是我替你定的，你多改改。"
（注意：参考图数量=0，全程不得出现 参考图 来源）\
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
