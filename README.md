# 纸墨讲解片

入口：[SKILL.md](SKILL.md)。

这是一份 skill，从已交付的讲解片《精神分析的本质》里提炼（5:29，1080p，三轮迭代 v1→v2→v3b）。它复刻那套做法：中文旁白的纸墨手绘风知识讲解片——米黄纸底、墨线手绘、唯一红色母题、思源黑体字幕，以及按实测配音时长驱动的时间轴。规则来自那次的代码、笔记和用户反馈。

## 目录

| 路径 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | 入口。阶段、每阶段的门、常见做坏方式 |
| [CHANGELOG.md](CHANGELOG.md) | 版本记录 |
| [references/](references/) | 开工前到交付前要读的笔记 |
| [scripts/](scripts/) | 引擎模板与开新片脚本。用法见 [scripts/README.md](scripts/README.md) |
| [examples/demo/](examples/demo/) | 成片截取的三段示范（人物 / 开幕闭幕 / 剪辑画面） |

`references/` 与 `SKILL.md` 里「先读哪份」对应：

- `feedback-lessons.md` — 用户反馈铁律（开工前必读）
- `narrative-patterns.md`、`accuracy-calibration.md` — 写稿与对照权威教材校准
- `style-bible.md` — 画面
- `pacing-and-audio.md`、`tts-pronunciation.md` — 时间轴、配音、混音、读音
- `qa-checklist.md`、`delivery.md` — 交付前自查与交付

`scripts/engine/` 是从原片泛化出的管线（纸、笔刷、配音、时间轴、渲染、配乐）。字体在 `scripts/engine/fonts/`（思源黑体 SC Medium / Bold）。`scripts/new_project.sh` 把引擎复制到新的项目目录。

## 当作 skill 使用

目录里已有 `SKILL.md`。agent 在用户说下面这些话时使用它（见该文件开头的 description）：

- 「做一部像《精神分析的本质》那样的讲解视频」
- 「纸墨/手绘风知识动画」
- 「用这个 skill 讲 XX」

从 [SKILL.md](SKILL.md) 读起，按其中的阶段打开 `references/`。改代码或开新片时读 [scripts/README.md](scripts/README.md)。不要在本 skill 目录里直接渲染；`new_project.sh` 会把引擎复制到 `/workspace/<slug>-film/`。

## 跑引擎

依赖、目录说明和三步流程都在 [scripts/README.md](scripts/README.md)。流程是：

1. `bash scripts/new_project.sh /workspace/<slug>-film`
2. 改复制过去的 `config.py`，写 `story.py` 和 `scenes_<x>.py`（函数 `scene_<场景id>(ctx, t)`）
3. 在引擎目录里 `python3 tts.py && python3 render.py still 3 10 20` 看静帧，再 `bash render_all.sh /workspace/<slug>-film <片名>`

依赖（原环境验证过的装法，详见 `scripts/README.md`）：`python3-cairo`（用 apt，不要用 pip 装 pycairo）、`edge-tts`、`pyloudnorm`、`scipy`、`pillow`、`numpy`，以及 ffmpeg。读音自检 `asr_check.py` 可选依赖 `faster-whisper`。

## 示例

[examples/demo/](examples/demo/) 里是三段从《精神分析的本质》v3 母带截取的短片（不是引擎冒烟测试），用来对照「想要的效果」：

| 片段 | 时长 | 示范 |
|---|---|---|
| [01_couch.mp4](examples/demo/01_couch.mp4) | 8 s | **人物怎么画** — 躺椅双人场面（分析师坐到病人看不见的地方） |
| [02_president.mp4](examples/demo/02_president.mp4) | 8 s | **开幕/闭幕节奏** — 议长宣布开幕→闭幕→「本来要说的，是开幕」 |
| [03_repress_nle.mp4](examples/demo/03_repress_nle.mp4) | 10 s | **剪辑画面** — 压抑讲解里片子自己的时间线与红门 |

静帧（各片段约 40% 处）：

- [01_couch.jpg](examples/demo/01_couch.jpg)
- [02_president.jpg](examples/demo/02_president.jpg)
- [03_repress_nle.jpg](examples/demo/03_repress_nle.jpg)

说明见 [examples/demo/README.md](examples/demo/README.md)。引擎端到端冒烟仍用 `scripts/engine/scenes_demo.py` 本地渲染，不必再进仓库示例目录。
