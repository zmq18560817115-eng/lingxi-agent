"""D0 预检 —— 五项检查，全通过则退出码 0。

对应文档 D0 完成定义："五项预检退出码全 0，最小链路通"。
运行：python preflight.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))


# 1. Python 版本
check("Python ≥ 3.10", sys.version_info >= (3, 10), sys.version.split()[0])

# 2. 关键依赖可导入
try:
    import fastapi, PIL, uvicorn  # noqa: F401
    check("依赖 fastapi/pillow/uvicorn 可导入", True)
except Exception as e:  # noqa: BLE001
    check("依赖 fastapi/pillow/uvicorn 可导入", False, str(e))

# 3. 四个服务可导入且签名存在
try:
    from services.analyze import analyze
    from services.parse import parse
    from services.render import render
    from services.brief import brief
    check("services 四件可导入", all(callable(f) for f in (analyze, parse, render, brief)))
except Exception as e:  # noqa: BLE001
    check("services 四件可导入", False, str(e))

# 4. fixtures 存在
lt = ROOT / "tests" / "fixtures" / "layout_tree_sample.json"
png = ROOT / "tests" / "fixtures" / "sample_1080x1440.png"
check("fixtures 存在", lt.exists() and png.exists(), f"{lt.exists()=} {png.exists()=}")

# 5. 假 PNG 尺寸必须是 1080×1440
try:
    from PIL import Image
    with Image.open(png) as im:
        check("样图尺寸 1080×1440", im.size == (1080, 1440), str(im.size))
except Exception as e:  # noqa: BLE001
    check("样图尺寸 1080×1440", False, str(e))

failed = 0
for name, ok, detail in checks:
    mark = "✓" if ok else "✗"
    print(f"[{mark}] {name}" + (f"  ({detail})" if detail else ""))
    failed += 0 if ok else 1

print("-" * 32)
print("全部通过 ✓" if failed == 0 else f"失败 {failed} 项 ✗")
sys.exit(0 if failed == 0 else 1)
