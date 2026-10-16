# 交付

## 文件
- 母带：`render_all.sh` 出 `<片名>.mp4`（chunk CRF 19 + AAC 192k，5:29 约 147–156MB）。
- 分享版：`encode_share.sh`：libx264 `-preset slow -crf 23 -tune animation -maxrate 1.2M -bufsize 2.4M`，AAC 128k，`+faststart`，5 分半约 37–47MB。超标就 CRF+2。

## 上限（原片踩过）
| 通道 | 上限 | 做法 |
|---|---|---|
| 聊天附件 | ≤200MB | 一般发分享版；群聊只能发文字，视频走私聊 |
| Drive UploadFile | ≤100MB/文件 | 发分享版；用户喜欢「传到网盘就行」给链接 |
| CopyFromBox | ≤100MB，大文件易超时 | 用户拒绝过分块拷贝，别主动提 |
| 整个工程打包 | ~4GB | zip 分卷 95MB/卷传 Drive 文件夹 + README；用 7-Zip 解压（`zip -s 0` 合并会损坏大 mp4） |
| GitHub | 单文件 100MB、仓库建议 <1GB | 大文件走 LFS 或 Release；需要用户在私聊授权 |

## 交付语
- 短：链接 + 时长 + 这一版改了什么（逐条对应用户意见）+ 诚实的未尽事项。
- 不剧透隐藏细节；用户问了再给清单（母题时间码＋口误时间码）。
- 用户说「还不认为这是成片」时，别推进打包/归档类动作。
