"""F4 渲染 —— 布局树 → 1080×1440 PNG。

【D4 真件】用 Pillow 按 parse() 的布局树真实绘制：标题栏、分组标签、
产品卡、价格条，配色取布局树的调色板，标题文字取需求方填的品牌/用途。
输出严格 1080×1440。

接口签名与 D1 假件一致：render(requirement_id) -> str。
IO 契约（文档 D4）：布局树 → PNG，与界面无关。
"""

from __future__ import annotations

import glob
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import store
from services.parse import parse

# 跨平台中文字体查找：Windows / Linux / macOS 常见 CJK 字体。
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",     # 黑体
    "C:/Windows/Fonts/simsun.ttc",     # 宋体
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",       # 文泉驿正黑
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",                 # macOS
]


def _find_font_path() -> str | None:
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return p
    hits = glob.glob("/usr/share/fonts/**/*zenhei*", recursive=True) or glob.glob(
        "/usr/share/fonts/**/*CJK*", recursive=True
    )
    return hits[0] if hits else None


_FONT_PATH = _find_font_path()


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if _FONT_PATH:
        try:
            return ImageFont.truetype(_FONT_PATH, size)
        except Exception:  # noqa: BLE001
            pass
    return ImageFont.load_default()  # 无 CJK 字体时兜底（中文可能显示为方块）


def _centered(draw: ImageDraw.ImageDraw, box, text: str, font, fill: str) -> None:
    x0, y0, x1, y1 = box
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((x0 + (x1 - x0 - (r - l)) / 2, y0 + (y1 - y0 - (b - t)) / 2 - t), text, font=font, fill=fill)


def render(requirement_id: str) -> str:
    req = store.get(requirement_id) or {}
    ref = (req.get("ref_paths") or [""])[0]
    tree = parse(ref)

    canvas = tree["canvas"]
    W, H = canvas["width"], canvas["height"]
    palette = tree.get("palette", {})
    primary = palette.get("primary", "#F5B841")
    text_col = palette.get("text", "#3A3226")
    bg = canvas.get("bg", palette.get("bg", "#FFF9EF"))

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    title_text = req.get("goal") or req.get("brand") or "视觉预览"

    for region in tree.get("regions", []):
        role = region.get("role")
        box = region.get("box", [0, 0, 0, 0])
        if role == "title_bar":
            d.rectangle(box, fill=primary)
            _centered(d, box, title_text, _font(56), "#FFFFFF")
        elif role == "group":
            label = region.get("label", "")
            if label:
                d.text((box[0], box[1] - 44), label, font=_font(32), fill=text_col)
            for card in region.get("children", []):
                cb = card.get("box", box)
                d.rounded_rectangle(cb, radius=16, fill="#FFFFFF", outline="#E6DCC6", width=2)
                for sub in card.get("children", []):
                    if sub.get("role") == "price_bar":
                        d.rounded_rectangle(sub.get("box", cb), radius=8, fill=primary)

    out_path = store.artifact_dir(requirement_id) / "render.png"
    img.save(out_path)
    return str(out_path)
