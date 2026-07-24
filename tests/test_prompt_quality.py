"""F2 拆解质量回归 —— 验证 SYSTEM_PROMPT 的来源判定是否达标。

只在**真 LLM 可用**时实测（需 ANTHROPIC_API_KEY）；否则整体跳过、退出码 0，
不影响无 Key 环境的 CI/预检。改完 prompt 后跑这个，一眼看出拆解质量有没有退。

运行：
  set /export ANTHROPIC_API_KEY=...   # 你的 Key
  python tests/test_prompt_quality.py

断言的是**规则**（不管模型措辞怎么变都该成立），不是逐字匹配：
  1. 参考图数量为 0 时，任何字段都不得出现「参考图」来源（硬护栏）
  2. 纯模糊输入（"干净点就行"）→ 色调/构图/排版必须标「默认推断」，不许伪装成明说
  3. 明说方向（"暖色""多留白"）→ 对应字段标「文字描述」
  4. 没提规避 → avoid 留空，不得凭空编
  5. 所有 source 落在允许的四类内；key_elements 非空
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("LINGXI_DATA_DIR", tempfile.mkdtemp(prefix="lingxi-pq-"))

import store  # noqa: E402
from services.analyze import analyze  # noqa: E402

ALLOWED = {"文字描述", "用户选项", "默认推断", "参考图"}


def _run(req: dict):
    rid = store.new_id()
    store.save(rid, req)
    return analyze(rid)


def _sources_ok(spec) -> list[str]:
    errs = []
    for name, f in [("色调", spec.tone), ("构图", spec.composition), ("排版", spec.layout)]:
        if f.source not in ALLOWED:
            errs.append(f"{name} 来源非法：{f.source}")
    if not spec.key_elements:
        errs.append("key_elements 为空")
    return errs


CASES = [
    {
        "name": "A 明说暖色 + 留白（无参考图）",
        "req": {"brand": "某吸奶器评测", "goal": "6款产品专业评测封面",
                "description": "专业评测、色调小清新不要太深、适当留白", "avoid": "暗黑风、深色底"},
        "checks": [
            ("色调应标 文字描述（'小清新暖色'是原话方向）",
             lambda s: s.tone.source == "文字描述"),
            ("无参考图时不得出现 参考图 来源",
             lambda s: all(f.source != "参考图" for f in (s.tone, s.composition, s.layout))),
            ("规避应包含 暗黑风",
             lambda s: any("暗黑" in a for a in s.avoid)),
        ],
    },
    {
        "name": "B 几乎全模糊：'干净点就行'（无参考图）",
        "req": {"brand": "山野手冲咖啡", "goal": "菜单头图", "description": "干净点就行", "avoid": ""},
        "checks": [
            ("色调必须标 默认推断（'干净'太宽泛，不许伪装成明说）",
             lambda s: s.tone.source == "默认推断"),
            ("构图必须标 默认推断",
             lambda s: s.composition.source == "默认推断"),
            ("没提规避 → avoid 应留空，不得凭空编",
             lambda s: len(s.avoid) == 0),
            ("无参考图时不得出现 参考图 来源",
             lambda s: all(f.source != "参考图" for f in (s.tone, s.composition, s.layout))),
        ],
    },
    {
        "name": "C 明说多留白、简洁（无参考图）",
        "req": {"brand": "极简科技海报", "goal": "新品发布主视觉", "description": "大量留白、简洁、现代", "avoid": ""},
        "checks": [
            ("构图提到留白且标 文字描述",
             lambda s: "留白" in s.composition.value and s.composition.source == "文字描述"),
            ("无参考图时不得出现 参考图 来源",
             lambda s: all(f.source != "参考图" for f in (s.tone, s.composition, s.layout))),
        ],
    },
]


def main() -> int:
    probe = _run({"brand": "探针", "goal": "x", "description": "暖色", "avoid": ""})
    if probe.generation_mode != "model":
        print("⏭  跳过：真 LLM 不可用（generation_mode=%s）。设 ANTHROPIC_API_KEY 后再跑。"
              % probe.generation_mode)
        return 0

    total = fails = 0
    for case in CASES:
        spec = _run(case["req"])
        print(f"\n【{case['name']}】 mode={spec.generation_mode}")
        for e in _sources_ok(spec):  # 通用检查：来源合法性 + key_elements 非空
            total += 1; fails += 1
            print(f"  ✗ {e}")
        for desc, check in case["checks"]:
            total += 1
            try:
                ok = check(spec)
            except Exception as ex:  # noqa: BLE001
                ok = False; desc += f"（异常：{ex}）"
            print(f"  {'✓' if ok else '✗'} {desc}")
            if not ok:
                fails += 1
                # 打印实际值，方便定位是模型标错还是 prompt 要补规则
                print(f"      实际：色调={spec.tone.source} 构图={spec.composition.source} "
                      f"排版={spec.layout.source} avoid={spec.avoid}")

    print("\n" + "-" * 40)
    print(f"通过 {total - fails}/{total}" + ("　全部达标 ✓" if fails == 0 else f"　失败 {fails} 项 ✗"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
