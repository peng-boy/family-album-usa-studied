# 走遍美国学习版

> 《走遍美国》(Family Album U.S.A.) 英语学习版：26 集完整台词、逐句中文翻译、音频播放、全局搜索，纯前端无后端，开箱即用。

---
## ⚠️ 版权声明与免责说明

如原作者或出版社认为本项目侵犯了相关权益，请通过 GitHub Issues 联系，本人将立即删除相关内容。

---


## 功能特性

- **26 集 / 78 幕 / 6000+ 句台词**：完整覆盖《走遍美国》全剧集
- **逐句中文翻译**：英文与中文对照显示，可一键切换显隐
- **音频同步高亮**：根据音频实际进度高亮当前台词，支持拖动进度、倍速和暂停；同时间戳台词同时高亮
- **台词定位播放**：点击台词（或聚焦后按 Enter / 空格）从该句播放，可开关自动滚动跟随
- **播放速度控制**：0.5× / 0.75× / 1× / 1.25× / 1.5× 五档可调
- **播放模式**：连续播放、单句一次、单句循环；点击台词选句，单句范围至下一个不同时间戳，最后一句至音频结束，同时间戳合并播放。单句一次结束暂停并回到句首，单句循环持续重复，原生暂停按钮可随时暂停
- **A–B 区间循环**：播放或拖动到起点点“设为 A 点”，到终点点“设为 B 点”，自动启用区间循环；B 至少比 A 晚 0.2 秒。暂停后可自由拖动，恢复播放回到区间；“清除 A–B”退出循环。切换集/幕清除设点
- **移动端底部播放卡片**：单行紧凑布局，仅展示播放/暂停、倍速、播放模式和“跟随”（高亮表示开启），不显示音频进度条或冗长提示；选择 A–B 循环时才展开设点控件。卡片固定到底部并避开安全区域，自动预留正文空间；桌面保留原生进度条。搜索、主题和翻译入口保留在顶部
- **全局搜索**：跨 26 集搜索英文台词、中文翻译或集名，点击跳转（`Ctrl/Cmd + K` 唤起）
- **响应式设计**：桌面双栏、手机底部播放卡片
- **纯静态部署**：无需后端，可直接托管到 GitHub Pages

---

## 在线预览

本项目可直接部署到 GitHub Pages，无需后端服务器：

**[👉 在线演示](https://peng-boy.github.io/family-album-usa-studied/)**

> 部署方式见下方「GitHub Pages 部署」章节。推送 `main` 分支后，仓库自带的 GitHub Actions workflow 会自动部署。

---

## 项目结构

```
family-album-usa-studied/
├── audio-acts/          # 78 个独立音频文件（每幕一个 mp3）
│   ├── e01_a1.mp3
│   ├── e01_a2.mp3
│   └── ... (e01 ~ e26，每集 3 个)
├── episodes.json        # 剧集数据（英文基于原版，中文翻译原创）
├── index.html           # 单页应用（完全原创代码）
├── .nojekyll            # 禁用 GitHub Pages 的 Jekyll 处理
├── .github/workflows/   # 自动部署到 GitHub Pages 的 workflow
└── README.md            # 本文件
```

### 数据格式

```json
{
  "episodes": [{
    "id": 1,
    "title": "46 Linden Street",
    "titleCn": "林登大街46号",
    "summary": "剧情简介...",
    "acts": [{
      "label": "Act I",
      "audio": "audio-acts/e01_a1.mp3",
      "hasAudio": true,
      "lineCount": 86,
      "lines": [{
        "t": 34.18,
        "en": "Excuse me. My name is Richard Stewart.",
        "cn": "打扰一下，我叫 Richard Stewart。"
      }]
    }]
  }]
}
```

**音频播放说明**：
- 每幕使用独立的 MP3 文件（`audio-acts/e{集数}_a{幕数}.mp3`）
- 台词时间戳 `t` 是相对该幕音频起始时间的偏移量（秒）

---

## 本地使用

### 方式一：直接打开（基础功能）

用浏览器直接打开 `index.html` 文件即可查看，但部分浏览器会因安全策略拦截 `fetch('episodes.json')`，**推荐使用方式二**。

### 方式二：本地服务器（推荐）

使用 Node.js 运行内置开发服务器，无需安装依赖，支持音频 Range 请求（拖动进度、逐句跳转）：

```bash
node dev-server.cjs
# 然后访问 http://127.0.0.1:8080
```

更换端口可设置环境变量 `PORT`（PowerShell：`$env:PORT=8081; node dev-server.cjs`）。修改前端文件后刷新浏览器即可生效。

运行自动测试（Node.js 22.18+ / 24+，不创建测试子进程）：

```bash
node --test --test-isolation=none tests/audio-sync.test.cjs
```

浏览器集成测试：启动服务后访问 `http://127.0.0.1:8080/tests/browser-smoke.html`，成功时显示 PASS。

高亮使用现有台词起始时间戳，持续至下一时间戳；片头及播放结束时不高亮。数据没有逐句结束时间，因此句间停顿会保留上一句高亮，精度取决于原始时间戳。

---

## 批量核对与校准台词时间

本地语音识别仅用于开发，静态网页不需要这些依赖；音频不会上传。

```bash
python -m pip install --target .tools/speech faster-whisper
# 识别第3–26集，每幕结束保存缓存与候选结果，可断点续跑
python tools/batch-calibrate.py --start 3 --end 26
# 调整对齐规则后复用缓存，不重复识别
python tools/batch-calibrate.py --start 3 --end 26 --align-only
# 检查候选数据与音频、文本、算法版本一致，默认只预检
python tools/apply-calibration.py
# 审核后显式应用通过门槛的幕，自动备份现有数据
python tools/apply-calibration.py --apply
# 校准程序的安全回归测试
python -m unittest discover -s tests -p test_batch_calibration.py
```

首次运行需下载英文模型到 `.tools/models`。缓存包含音频 SHA-256 与模型名；换音频会重新识别。逐幕结果在 `diagnostics/batch/`，汇总为 `summary.json`，候选数据为 `diagnostics/episodes-calibrated.json`。默认**不覆盖** `episodes.json`。

校准不是简单地减去统一偏移：程序匹配台词和词级识别时间，标记场景断点、长词吞静默、低覆盖及缺失句。插值/短距离外推一律标记待复核；不安全的场景间隔不插值。多个独特长句锚点若在整幕范围形成紧密的固定偏移簇，可用该偏移估算短句，仍标记待复核。存在未确认断点、偏移冲突、无法形成完整有序时间轴或可靠锚点不足的幕不应用候选，保留当前数据。`eligible` 表示通过机器应用门槛，不代表人工验收或逐句精确。应用前会再次核对算法、台词及音频的哈希；实际应用记录在 `diagnostics/batch/application-receipt.json`。

### 本次批量结果

第3–26集72幕（5813条台词）已全部完成本地识别和机器对齐检查：15幕、1226条台词通过保守门槛并应用；57幕保留原时间等待复核。其中已应用部分仍有708条短句/低置信条目采用估计并明确标记，不等同逐句人工验收。第1、2集原有校准未改动。

已应用：第3集I；第4集I/II；第5集I/II/III；第6集III；第7集I/III；第8集II/III；第9集II；第10集I/II/III。

第18集II/III与第19集全部三幕原时间全部为0，部分台词含说话人标签，不能靠统一偏移修复。其他未通过项包含场景断点、粗估时间及识别缺失。完整清单和原因见 [批量校准报告](diagnostics/batch-calibration-report.md)。不能将整套课程视为已经精确同步。

## GitHub Pages 部署

本项目**纯静态**，可直接部署到 GitHub Pages，**完全免费**。

### 自动部署（推荐）

仓库已包含 `.github/workflows/deploy.yml`，推送 `main` 分支会自动部署：

1. Fork 本仓库到你自己的 GitHub 账号
2. 进入仓库 → **Settings** → **Pages**
3. **Source** 选择 **GitHub Actions**
4. 推送代码到 `main` 分支，等待 Actions 跑完即可访问：
   `https://你的用户名.github.io/family-album-usa-studied/`

---

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl/Cmd + K` | 打开 / 关闭搜索 |
| `Esc` | 关闭搜索弹窗 |

---

## 浏览器支持

- Chrome / Edge / Firefox / Safari 最新版
- 支持移动端浏览（手机、平板自适应）

### 移动端特性

- 底部导航栏：首页、搜索、主题切换、翻译切换
- 自适应字体：根据屏幕宽度自动调整文字大小
- 触控优化：按钮和台词区域适合手指点击

---

## 许可证

MIT

> 本项目仅供英语学习交流使用，不得用于商业用途。
