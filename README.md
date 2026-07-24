# lingxi-agent · 灵犀 · 需求翻译器

把需求方模糊的视觉诉求（自然语言 + 参考图）翻译成一份**能被人和机器双向确认**的视觉规格：
一段人话复述（F2）、一张 1080×1440 预览图（F4）、一份可交付说明书（F5）。

> 构建策略见《灵犀 · 构建策略与执行修订》。核心原则：**能走通 > 做得对 > 好不好看**。
> 采用纵向切片——D1 用假件把全链路铺通，D2–D5 每天拆掉一块假的换成真的。

## 当前进度

- **D0 ✓** 五项预检退出码全 0：`python preflight.py`
- **D1 ✓** 端到端假件骨架：填表 → 复述 → 确认 → 出图 → 导出，全假数据可点通
- **D2 ✓** F2 接真 LLM（Claude Opus 4.8 + 结构化输出）；断网/无 Key 自动降级 `rule_fallback`
- **D4 ✓** F4 渲染按布局树真实绘制（Pillow），标题取需求方输入、配色取调色板，稳定输出 1080×1440
- **联调 ✓** F2 复述缓存并回流：确认/改写 → 说明书用那版文字；确认的**色调色号 → 出图配色**；出图页图文同屏、去开发术语
- **D5 ✓** 说明导出：一页 HTML 说明书（内嵌预览图 + 规格表 + 来源标注，可打印成 PDF）/ Markdown / JSON，均可下载
- **打磨 ✓** F2 逐字段纠偏：色调/构图/排版/关键元素/规避各自可改，改动来源标「用户修改」并回流到出图与说明书；各页加加载/错误/提交状态
- D3：见下方「模块与替换路线」

> **D2 运行前提**：真 LLM 路径需要在你的环境里设置 `ANTHROPIC_API_KEY`。
> 没有 Key 时不会报错——`analyze()` 自动走规则兜底（`generation_mode=rule_fallback`），
> 前端复述区照常显示，只是文案由规则草拟而非模型生成。

## 运行

```bash
pip install -r requirements.txt
python preflight.py            # D0 预检，应全 ✓
python main.py                 # 打开 http://127.0.0.1:8000/
```

`python main.py` 内置了启动入口，能绕开部分 Windows 安全策略对 `uvicorn.exe` 的拦截。
也可直接 `uvicorn main:app --reload`（若未被拦截）。

**Windows PowerShell 用户注意**（命令与 bash 不同）：

```powershell
git clone https://github.com/zmq18560817115-eng/lingxi-agent.git
cd lingxi-agent
git checkout claude/project-architecture-understanding-29vvds
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-你的真实key"   # 设环境变量用 $env:，不是 export
python main.py                                  # 不要用 uvicorn.exe（可能被安全策略拦）
```

测试（需 dev 依赖）：

```bash
pip install -r requirements-dev.txt
python tests/test_skeleton.py  # 端到端骨架冒烟测试；或 python -m pytest tests/ -q
```

**F2 拆解质量回归**（改完 `analyze.py` 的 prompt 后跑）：

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # 有 Key 才实测；没 Key 自动跳过、退出码 0
python tests/test_prompt_quality.py
```

断言的是来源判定**规则**（无参考图不得标「参考图」、纯模糊输入必须标「默认推断」、
明说方向标「文字描述」、没提规避则 avoid 留空），失败会打印实际来源便于定位。

## 结构

```
main.py              FastAPI 入口，路由 = 纵向切片的接缝（D2–D5 不改路由）
models.py            数据契约：Sourced / VisualSpec / Brief / Requirement
store.py             按 requirement_id 的 JSON 文件存储
services/
  analyze.py   F2 理解复述   analyze(requirement_id) -> VisualSpec   【D1 假件】
  parse.py     F3 版式解析   parse(ref_path) -> dict                【D1 假件】
  render.py    F4 渲染       render(requirement_id) -> str (png)     【D1 假件】
  brief.py     F5 说明导出   brief(requirement_id) -> Brief          【D1 假件】
web/                 原生 HTML 最小前端（restate.html 是唯一认真做的页）
tests/fixtures/      layout_tree_sample.json（D3 目标产物）+ sample_1080x1440.png
preflight.py         D0 五项预检
```

## 模块与替换路线

| 模块 | 服务 | 现状 | 替换点 |
|---|---|---|---|
| F2 理解复述 | `services/analyze.py` | **✓ 真 LLM（Opus 4.8）+ 规则兜底** | 已完成（D2） |
| F3 版式解析 | `services/parse.py` | 读 fixture | **D3** 真识别「标题栏 + N×M 网格」 |
| F4 渲染 | `services/render.py` | **✓ Pillow 按布局树绘制 1080×1440** | 已完成（D4） |
| F5 说明导出 | `services/brief.py` | **✓ HTML/Markdown/JSON，内嵌预览图 + 来源标注** | 已完成（D5） |

替换时**只改 service 内部实现，不改函数签名与路由**——这是骨架能一直可演示的前提。
假件保留在服务内标注 `【D1 假件】`，兼作 D5 的降级兜底。
