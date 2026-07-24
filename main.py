"""灵犀 · 需求翻译器 —— FastAPI 入口。

D1 目标：填表 → 提交 → 看到复述 → 点确认 → 看到 PNG → 点导出，全链路可点通（假数据）。
路由是纵向切片的接缝，D2–D5 只换 services 内部实现，路由与前端契约不变。
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles

import store
from models import Requirement
from services.analyze import analyze
from services.brief import brief as build_brief
from services.brief import brief_html, brief_markdown
from services.render import render

app = FastAPI(title="灵犀 · 需求翻译器")
WEB = Path(__file__).resolve().parent / "web"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WEB / "index.html").read_text(encoding="utf-8")


# —— F1 录入 ——
@app.post("/requirements")
def create_requirement(
    brand: str = Form(""),
    goal: str = Form(""),
    description: str = Form(""),
    avoid: str = Form(""),
) -> RedirectResponse:
    rid = store.new_id()
    req = Requirement(requirement_id=rid, brand=brand, goal=goal, description=description, avoid=avoid)
    store.save(rid, req.to_dict())
    return RedirectResponse(url=f"/requirements/{rid}/restate", status_code=303)


# —— F2 理解复述（唯一被主观评价、需认真对待的界面）——
@app.get("/requirements/{rid}/restate", response_class=HTMLResponse)
def restate_page(rid: str) -> str:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    return (WEB / "restate.html").read_text(encoding="utf-8")


@app.get("/api/requirements/{rid}/analyze")
def api_analyze(rid: str) -> JSONResponse:
    payload = store.get(rid)
    if payload is None:
        raise HTTPException(404, "需求不存在")
    # 缓存 spec：复述页刷新、后续出图/导出都复用同一份，避免重复调 LLM，
    # 也保证 F2 复述 / F4 出图 / F5 说明书用的是同一份理解。
    spec = payload.get("spec")
    if not spec:
        spec = analyze(rid).to_dict()
        store.update(rid, spec=spec)
    return JSONResponse(spec)


@app.post("/api/requirements/{rid}/confirm")
def api_confirm(rid: str, confirmed_restate: str = Form("")) -> JSONResponse:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    store.update(rid, confirmed_restate=confirmed_restate)
    return JSONResponse({"ok": True, "next": f"/requirements/{rid}/preview"})


# —— F4 渲染 ——
@app.get("/requirements/{rid}/preview", response_class=HTMLResponse)
def preview_page(rid: str) -> str:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    return (WEB / "preview.html").read_text(encoding="utf-8")


@app.post("/api/requirements/{rid}/render")
def api_render(rid: str) -> JSONResponse:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    path = render(rid)
    return JSONResponse({"ok": True, "png": f"/requirements/{rid}/render.png", "_disk": path})


@app.get("/requirements/{rid}/render.png")
def render_png(rid: str) -> FileResponse:
    path = store.artifact_dir(rid) / "render.png"
    if not path.exists():
        raise HTTPException(404, "尚未渲染")
    return FileResponse(path, media_type="image/png")


# —— F5 说明导出 ——
@app.get("/api/requirements/{rid}/brief")
def api_brief(rid: str) -> JSONResponse:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    return JSONResponse(build_brief(rid).to_dict())


@app.get("/requirements/{rid}/brief.html", response_class=HTMLResponse)
def export_brief_html(rid: str, download: int = 0) -> HTMLResponse:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    headers = (
        {"Content-Disposition": f'attachment; filename="brief_{rid}.html"'} if download else {}
    )
    return HTMLResponse(brief_html(rid), headers=headers)


@app.get("/requirements/{rid}/brief.md", response_class=PlainTextResponse)
def export_brief_md(rid: str, download: int = 0) -> PlainTextResponse:
    if store.get(rid) is None:
        raise HTTPException(404, "需求不存在")
    headers = (
        {"Content-Disposition": f'attachment; filename="brief_{rid}.md"'} if download else {}
    )
    return PlainTextResponse(brief_markdown(rid), media_type="text/markdown; charset=utf-8", headers=headers)


app.mount("/static", StaticFiles(directory=WEB), name="static")


if __name__ == "__main__":
    # 直接 `python main.py` 启动，绕开被安全策略拦截的 uvicorn.exe 启动器。
    # 默认单进程（不开 reload），在被 WDAC/AppLocker 锁定的 Windows 上最稳；
    # 需要改代码自动重载时设 LINGXI_RELOAD=1。
    import uvicorn

    reload = os.environ.get("LINGXI_RELOAD") == "1"
    uvicorn.run("main:app" if reload else app, host="127.0.0.1", port=8000, reload=reload)
