# 引擎模板

从 `/workspace/psychoanalysis-film-v3/` 泛化：去掉了题材相关的场景与道具，保留整条管线。

```
engine/
  config.py        片名、场景模块、音色、字幕参数、响度、编码参数
  story.py         ★唯一真相源：场景 → beats（停顿/旁白/口误/颤动/say 同音替换）
  scenes_demo.py   ★示范场景（新片换成自己的 scenes_*.py，并写进 config.SCENE_MODULES）
  ink.py           纸、笔刷 stroke、fill_poly、hatch、文字 text/write_on/text_halo、camera、red_door 母题登记
  figs.py          ls/le/wt 取时、sp 分步、气泡、箭头、圈注、卡片、nested（画片子自己的某一帧）
  tts.py           edge-tts → 去静音 wav → tts/durations.json
  timeline.py      实测时长 → 场景/句子起止
  render.py        info | still t.. | chunk f0 f1 out | scan
  audio.py         numpy 配乐 + 闪避 + 问句后静音 + -16 LUFS → out/mix.wav
  asr_check.py     whisper 读音自检（可选依赖 faster-whisper）
  render_all.sh    一键：tts→scan→audio→并行渲染→母带→分享版→静帧
  encode_share.sh  <100MB 分享编码
  stills.py        按时间轴抽 QA 静帧 + contact.jpg
  fonts/           思源黑体 SC Medium / Bold
new_project.sh     复制引擎到项目目录并检查依赖
```

## 新片三步
1. `bash new_project.sh /workspace/<slug>-film`
2. 改 `config.py`、写 `story.py`、写 `scenes_<x>.py`（函数 `scene_<场景id>(ctx, t)`；先 `paper(ctx,t)`，世界坐标作画，`camera()` 取景，时间用 `ls/le/wt`）。
3. `python3 tts.py && python3 render.py still 3 10 20` 看静帧 → `bash render_all.sh /workspace/<slug>-film <片名>`。

## 依赖（box 上验证过）
`sudo apt-get install -y python3-cairo`（pip 装 pycairo 会失败）；`pip install --user --break-system-packages -U edge-tts pyloudnorm scipy pillow numpy`；ffmpeg。

## 性能
14.7s 示范（`scenes_demo.py`）在 8 核上全流程约 20s。原片 5:29（~9900 帧）8 进程并行渲染。改一处只想看效果时用 `render.py still`，别全片重渲。

## 仓库里的画面示例
[`examples/demo/`](../examples/demo/) 是从《精神分析的本质》v3 **成片截取**的三段（躺椅双人、议长开幕闭幕、压抑讲解里的剪辑台），用来对照人物画法、开幕闭幕节奏和自指剪辑画面——不是 `scenes_demo.py` 冒烟测试的输出。本地验证引擎仍跑 `scenes_demo.py`。

## 原片里还有、模板没带的（需要时去原工程抄）
- `scenes_b.py` 剪辑时间线自指装置、凝缩脸、移置房间；`scenes_c.py` 躺椅、联想链、揭示蒙太奇（×N 计数器、证据拼成门）、开门结尾完整版
- `figs.nested()` 用于在画面里放片子自己过去的某一帧（揭示回放）
- `audio.py` 原版：倒放回声（用自身混音倒放加速做倒带声）、心跳脉冲、按 doors.json 放母题
- `cand3.py` 同音字候选 × 多模型 ASR 投票；`audio_diptest.py` 呼吸处压 pad 的 A/B
