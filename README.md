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
| [examples/demo/](examples/demo/) | 14.7 秒端到端冒烟测试 |

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

[examples/demo/demo.mp4](examples/demo/demo.mp4) 是引擎模板的 **14.7 秒**端到端冒烟测试（两场景，见 `scripts/engine/scenes_demo.py`；`CHANGELOG.md` 记的是这次测试）。同一条片子上的静帧：

- [5.6 秒](examples/demo/stills/5.6.jpg)
- [8.0 秒](examples/demo/stills/8.0.jpg)
- [13.2 秒](examples/demo/stills/13.2.jpg)
