"""F4 渲染 —— 布局树 → 1080×1440 PNG。

【D1 假件】把 fixtures/sample_1080x1440.png 拷到产物目录并返回路径。
尺寸必须是真的 1080×1440，否则前端布局白调。
D4 替换：用 Pillow 按 parse() 的布局树真实绘制，输出同尺寸 PNG。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import store

SAMPLE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_1080x1440.png"


def render(requirement_id: str) -> str:
    # D4 起：取 parse() 布局树 + analyze() 视觉规格 → Pillow 绘制 → 写出 PNG。
    # D1 直接拷贝固定样图。
    out_path = store.artifact_dir(requirement_id) / "render.png"
    shutil.copy(SAMPLE, out_path)
    return str(out_path)
