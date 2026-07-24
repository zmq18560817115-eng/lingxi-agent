"""灵犀 · 核心数据契约

这些结构是 F2/F3/F4/F5 之间的接口。D1 用假件填充，D2–D5 只换生产实现、
不改这里的字段与类型。任何字段变动都是一次跨模块的契约变更，需谨慎。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

# 每个视觉判断的来源，用于可解释性：需求方能看清"这条是你说的 / 你选的 / 我猜的"。
SourceKind = Literal["文字描述", "用户选项", "默认推断", "参考图"]


@dataclass
class Sourced:
    """带来源的取值。value 是结论，source 是它从哪来。"""

    value: str
    source: SourceKind = "默认推断"

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "source": self.source}


@dataclass
class VisualSpec:
    """F2 的产物：把模糊需求翻译成的结构化视觉规格 + 一段人话复述。

    restate 是全产品价值所在——它是唯一会被需求方主观评价的字段。
    """

    tone: Sourced          # 色调
    composition: Sourced   # 构图
    layout: Sourced        # 排版
    key_elements: list[str] = field(default_factory=list)   # 关键元素
    avoid: list[str] = field(default_factory=list)          # 明确规避
    restate: str = ""      # 给人看的一段口语化复述
    generation_mode: Literal["model", "rule_fallback"] = "model"  # 真 LLM / 断网降级

    def to_dict(self) -> dict[str, Any]:
        return {
            "tone": self.tone.to_dict(),
            "composition": self.composition.to_dict(),
            "layout": self.layout.to_dict(),
            "key_elements": list(self.key_elements),
            "avoid": list(self.avoid),
            "restate": self.restate,
            "generation_mode": self.generation_mode,
        }


@dataclass
class Brief:
    """F5 的产物：可交付给设计/生产方的说明书。"""

    title: str
    summary: str           # 一句话概述
    tone: str
    composition: str
    layout: str
    key_elements: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    reference_note: str = ""   # 参考图的使用边界（借版式 / 不沿用配色 等）

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Requirement:
    """F1 录入的原始需求，按 requirement_id 存储，串起后续所有服务。"""

    requirement_id: str
    brand: str = ""            # 品牌 / 产品名
    goal: str = ""             # 用途（如：专业评测封面）
    description: str = ""       # 需求方的原话
    avoid: str = ""            # 不想要什么
    ref_paths: list[str] = field(default_factory=list)  # 参考图路径
    confirmed_restate: str = ""  # F2 纠偏后需求方确认/改写的复述

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
