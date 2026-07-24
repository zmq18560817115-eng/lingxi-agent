"""F4 渲染 —— 布局树 → 1080×1440 PNG。

【D4 真件 · 多版式】按 parse() 的布局树递归绘制，支持多种版式的角色词汇：
标题栏 / 分组 / 产品卡 / 网格格 / 价格条 / 主图区 / 文本块 / 列表行 / 分类头。
标题文字取需求方填的品牌/用途，配色取布局树调色板并跟随 F2 确认的色调。
输出严格 1080×1440。

接口签名与 D1 假件一致：render(requirement_id) -> str。
"""

from __future__ import annotations

import glob
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import store
from services.parse import parse

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
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


def _font(size: int):
    if _FONT_PATH:
        try:
            return ImageFont.truetype(_FONT_PATH, size)
        except Exception:  # noqa: BLE001
            pass
    return ImageFont.load_default()


def _centered(d, box, text, font, fill) -> None:
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    d.text((x0 + (x1 - x0 - (r - l)) / 2, y0 + (y1 - y0 - (b - t)) / 2 - t), text, font=font, fill=fill)


def _draw(d, region, ctx) -> None:
    """按角色画一个区域，然后递归子区域（唯一递归点）。"""
    role = region.get("role")
    box = region.get("box", [0, 0, 0, 0])
    primary, text_col = ctx["primary"], ctx["text"]

    if role == "title_bar":
        d.rectangle(box, fill=primary)
        _centered(d, box, ctx["title"], _font(56), "#FFFFFF")
    elif role == "group":
        label = region.get("label", "")
        if label:
            d.text((box[0], box[1] - 44), label, font=_font(32), fill=text_col)
    elif role in ("product_card", "cell", "card"):
        d.rounded_rectangle(box, radius=16, fill="#FFFFFF", outline="#E6DCC6", width=2)
    elif role == "price_bar":
        d.rounded_rectangle(box, radius=8, fill=primary)
    elif role == "hero":
        d.rounded_rectangle(box, radius=16, fill="#FFFFFF", outline="#E6DCC6", width=2)
        _centered(d, box, "主图区", _font(40), "#C9BEA5")
    elif role == "text_block":
        d.rounded_rectangle(box, radius=12, fill="#FBF7EE", outline="#EFE7D4", width=2)
        x0, y0, x1, _y1 = box
        for i in range(3):  # 三条灰线示意文字
            ly = y0 + 28 + i * 34
            d.rounded_rectangle([x0 + 24, ly, x1 - (24 if i < 2 else 260), ly + 12], radius=6, fill="#E7DEC9")
    elif role == "list_row":
        d.rounded_rectangle(box, radius=10, fill="#FFFFFF", outline="#EFE7D4", width=2)
        x0, y0, x1, y1 = box
        cy = (y0 + y1) // 2
        d.rounded_rectangle([x0 + 20, cy - 8, x0 + 320, cy + 8], radius=6, fill="#ECE3CE")  # 条目名占位
        d.rounded_rectangle([x1 - 150, cy - 22, x1 - 24, cy + 22], radius=8, fill=primary)   # 价格条
    elif role == "category":
        d.rectangle([box[0], box[3] - 4, box[2], box[3]], fill=primary)  # 分类下划线
        d.text((box[0], box[1]), "分类", font=_font(30), fill=text_col)

    for child in region.get("children", []):
        _draw(d, child, ctx)


def render(requirement_id: str) -> str:
    req = store.get(requirement_id) or {}
    template = req.get("template", "two_col")
    ref = (req.get("ref_paths") or [""])[0]
    tree = parse(ref, template)

    canvas = tree["canvas"]
    W, Hh = canvas["width"], canvas["height"]
    palette = tree.get("palette", {})
    primary = palette.get("primary", "#F5B841")
    text_col = palette.get("text", "#3A3226")
    bg = canvas.get("bg", palette.get("bg", "#FFF9EF"))

    # 配色跟随 F2 确认的色调（从 tone 文案取色号）。
    spec = (store.get(requirement_id) or {}).get("spec") or {}
    hexes = re.findall(r"#[0-9A-Fa-f]{6}", spec.get("tone", {}).get("value", ""))
    if hexes:
        primary = hexes[0]
    if len(hexes) > 1:
        bg = hexes[1]

    img = Image.new("RGB", (W, Hh), bg)
    d = ImageDraw.Draw(img)
    ctx = {"primary": primary, "text": text_col,
           "title": req.get("goal") or req.get("brand") or "视觉预览"}
    for region in tree.get("regions", []):
        _draw(d, region, ctx)

    out_path = store.artifact_dir(requirement_id) / "render.png"
    img.save(out_path)
    return str(out_path)
