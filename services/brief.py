"""F5 说明导出 —— 汇总成可交付说明书。

【联调版】优先用缓存的 spec（F2 复述的产物），并把需求方**确认/改写**的
那版复述作为概述回流进来，保证说明书 = 需求方点头的那份理解。
没有缓存 spec 时兜底现算一次。
"""

from __future__ import annotations

import base64
import html
from datetime import date
from pathlib import Path

import store
from models import Brief
from services.analyze import analyze
from services.render import render


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


def _spec_of(requirement_id: str) -> dict:
    data = store.get(requirement_id) or {}
    return data.get("spec") or analyze(requirement_id).to_dict()


def brief_markdown(requirement_id: str) -> str:
    """给设计师看的 Markdown 说明书——可直接粘进飞书/Notion。"""
    b = brief(requirement_id)
    spec = _spec_of(requirement_id)

    def line(label: str, field: str) -> str:
        f = spec.get(field, {})
        return f"- **{label}**：{f.get('value','')}　〔来源：{f.get('source','')}〕"

    parts = [
        f"# {b.title}",
        "",
        f"> {b.summary}",
        "",
        "## 视觉规格",
        line("色调", "tone"),
        line("构图", "composition"),
        line("排版", "layout"),
        "",
        f"**关键元素**：{ '、'.join(b.key_elements) or '—' }",
        "",
        f"**明确规避**：{ '、'.join(b.avoid) or '—' }",
        "",
        f"**参考说明**：{b.reference_note}",
        "",
        f"_由灵犀生成 · {date.today().isoformat()}_",
    ]
    return "\n".join(parts)


def brief_html(requirement_id: str) -> str:
    """自带预览图的单页 HTML 说明书——可在浏览器打印成 PDF，或下载单文件发出。"""
    b = brief(requirement_id)
    spec = _spec_of(requirement_id)
    e = html.escape

    # 内嵌预览图（base64 data URI），保证是"单文件"，方便直接发给设计师。
    try:
        png = Path(render(requirement_id))
        data_uri = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
        img_html = f'<img class="preview" src="{data_uri}" alt="视觉预览">'
    except Exception:  # noqa: BLE001
        img_html = '<div class="preview placeholder">（预览图暂不可用）</div>'

    def row(label: str, field: str) -> str:
        f = spec.get(field, {})
        return (
            f'<tr><th>{e(label)}</th><td>{e(f.get("value",""))}'
            f'<span class="src">来源 · {e(f.get("source",""))}</span></td></tr>'
        )

    chips = lambda xs, cls: "".join(f'<span class="chip {cls}">{e(x)}</span>' for x in xs) or "—"

    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(b.title)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font: 15px/1.7 system-ui,-apple-system,"Microsoft YaHei",sans-serif; color:#3A3226;
         max-width:820px; margin:32px auto; padding:0 24px; background:#fff; }}
  h1 {{ font-size:24px; margin:0 0 4px; }}
  .meta {{ color:#9a8f78; font-size:13px; margin-bottom:20px; }}
  .summary {{ font-size:17px; background:#FFF9EF; border-left:4px solid #F5B841;
             padding:14px 18px; border-radius:8px; margin:18px 0 24px; }}
  .preview {{ width:100%; border:1px solid #e6dcc6; border-radius:10px; display:block; margin:16px 0 28px; }}
  .placeholder {{ padding:60px; text-align:center; color:#9a8f78; background:#faf6ec; }}
  h2 {{ font-size:16px; border-bottom:2px solid #F5B841; padding-bottom:6px; margin:28px 0 12px; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ text-align:left; width:88px; padding:10px 8px; vertical-align:top; color:#6b6250; font-weight:600; }}
  td {{ padding:10px 8px; border-bottom:1px solid #f0e9d8; }}
  .src {{ display:block; font-size:12px; color:#9a8f78; margin-top:3px; }}
  .chip {{ display:inline-block; padding:4px 12px; border-radius:999px; font-size:13px;
          margin:4px 6px 0 0; background:#F5EFE0; }}
  .chip.avoid {{ background:#fbe6e2; color:#a3392b; }}
  footer {{ margin-top:36px; color:#9a8f78; font-size:12px; border-top:1px solid #eee; padding-top:12px; }}
  @media print {{ body {{ margin:0; max-width:none; }} .noprint {{ display:none; }} }}
</style></head>
<body>
  <h1>{e(b.title)}</h1>
  <div class="meta">灵犀 · 需求翻译器　|　{date.today().isoformat()}</div>
  <div class="summary">{e(b.summary)}</div>

  <h2>预览效果（供设计师复刻版式与配色）</h2>
  {img_html}

  <h2>视觉规格</h2>
  <table>{row("色调","tone")}{row("构图","composition")}{row("排版","layout")}</table>

  <h2>关键元素（画面必须出现）</h2>
  <div>{chips(b.key_elements, "")}</div>

  <h2>明确规避</h2>
  <div>{chips(b.avoid, "avoid")}</div>

  <h2>参考说明</h2>
  <p>{e(b.reference_note)}</p>

  <footer>「来源」标注每条规格的依据：<b>文字描述</b>=需求方明说、<b>用户选项</b>=勾选推出、
  <b>默认推断</b>=系统按常识补、<b>参考图</b>=从参考图看出。推断项设计师可灵活处理，明说项请严格遵循。</footer>
</body></html>"""

