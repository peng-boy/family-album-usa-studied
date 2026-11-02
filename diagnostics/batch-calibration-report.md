# 第3–26集批量时间校准报告

实际已应用：15 幕（以 application-receipt.json 为准）。

这是机器辅助校准，不是逐句人工听校。音频在本机识别，没有上传。

- 已生成对齐报告：72 / 72 幕
- 通过当前自动应用门槛：15 幕
- 保留原轴、需进一步复核：57 幕
- 处理错误：0

通过门槛的候选仍可能含短句偏移估计，逐句 timingNeedsReview 标记和来源保留。
未通过的幕不混合新旧时间轴、不盲目跨过场插值；识别缓存可用于后续精校。

| 幕 | 自动应用候选 | 可靠锚点/句数 | 待复核句 | 阻断原因 |
|---|---|---:|---:|---|
| e03_a1 | 是 | 39/75 | 36 | — |
| e03_a2 | 否 | 44/80 | 36 | unresolved-lines |
| e03_a3 | 否 | 26/70 | 44 | unresolved-lines, insufficient-anchor-evidence |
| e04_a1 | 是 | 27/64 | 37 | — |
| e04_a2 | 是 | 16/53 | 37 | — |
| e04_a3 | 否 | 26/64 | 38 | unresolved-lines, insufficient-anchor-evidence, unreviewed-scene-discontinuity |
| e05_a1 | 是 | 28/77 | 49 | — |
| e05_a2 | 是 | 18/80 | 62 | — |
| e05_a3 | 是 | 38/80 | 42 | — |
| e06_a1 | 否 | 28/88 | 60 | unresolved-lines, insufficient-anchor-evidence, unreviewed-scene-discontinuity |
| e06_a2 | 否 | 22/58 | 36 | unresolved-lines, insufficient-anchor-evidence |
| e06_a3 | 是 | 46/112 | 66 | — |
| e07_a1 | 是 | 41/75 | 34 | — |
| e07_a2 | 否 | 47/89 | 42 | unresolved-lines, unreviewed-scene-discontinuity |
| e07_a3 | 是 | 61/117 | 56 | — |
| e08_a1 | 否 | 37/69 | 32 | unresolved-lines, unreviewed-scene-discontinuity |
| e08_a2 | 是 | 29/101 | 72 | — |
| e08_a3 | 是 | 33/75 | 42 | — |
| e09_a1 | 否 | 16/94 | 78 | insufficient-anchor-evidence |
| e09_a2 | 是 | 34/79 | 45 | — |
| e09_a3 | 否 | 60/103 | 43 | unresolved-lines |
| e10_a1 | 是 | 39/92 | 53 | — |
| e10_a2 | 是 | 47/93 | 46 | — |
| e10_a3 | 是 | 22/53 | 31 | — |
| e11_a1 | 否 | 39/77 | 38 | unresolved-lines, unreviewed-scene-discontinuity |
| e11_a2 | 否 | 69/110 | 41 | unresolved-lines, unreviewed-scene-discontinuity |
| e11_a3 | 否 | 50/98 | 48 | unresolved-lines |
| e12_a1 | 否 | 33/63 | 30 | unresolved-lines |
| e12_a2 | 否 | 33/62 | 29 | unresolved-lines, unreviewed-scene-discontinuity |
| e12_a3 | 否 | 77/141 | 64 | unresolved-lines, unreviewed-scene-discontinuity |
| e13_a1 | 否 | 40/97 | 57 | unresolved-lines, insufficient-anchor-evidence |
| e13_a2 | 否 | 25/50 | 25 | unresolved-lines |
| e13_a3 | 否 | 35/75 | 40 | unresolved-lines |
| e14_a1 | 否 | 52/93 | 41 | unresolved-lines |
| e14_a2 | 否 | 50/118 | 68 | unresolved-lines, insufficient-anchor-evidence |
| e14_a3 | 否 | 39/65 | 26 | unresolved-lines |
| e15_a1 | 否 | 39/79 | 40 | unresolved-lines |
| e15_a2 | 否 | 31/65 | 34 | unresolved-lines, unreviewed-scene-discontinuity |
| e15_a3 | 否 | 38/62 | 24 | unresolved-lines |
| e16_a1 | 否 | 46/83 | 37 | unresolved-lines |
| e16_a2 | 否 | 21/58 | 37 | unresolved-lines, insufficient-anchor-evidence |
| e16_a3 | 否 | 36/98 | 62 | unresolved-lines, insufficient-anchor-evidence |
| e17_a1 | 否 | 32/58 | 26 | unresolved-lines |
| e17_a2 | 否 | 35/71 | 36 | unresolved-lines, unreviewed-scene-discontinuity |
| e17_a3 | 否 | 19/44 | 25 | unresolved-lines, insufficient-anchor-evidence |
| e18_a1 | 否 | 78/120 | 42 | unresolved-lines, unreviewed-scene-discontinuity |
| e18_a2 | 否 | 0/38 | 38 | unresolved-lines, insufficient-anchor-evidence |
| e18_a3 | 否 | 0/46 | 46 | unresolved-lines, insufficient-anchor-evidence |
| e19_a1 | 否 | 0/62 | 62 | unresolved-lines, insufficient-anchor-evidence |
| e19_a2 | 否 | 0/38 | 38 | unresolved-lines, insufficient-anchor-evidence |
| e19_a3 | 否 | 0/13 | 13 | unresolved-lines, insufficient-anchor-evidence |
| e20_a1 | 否 | 37/73 | 36 | unresolved-lines |
| e20_a2 | 否 | 48/92 | 44 | unresolved-lines, unreviewed-scene-discontinuity |
| e20_a3 | 否 | 51/112 | 61 | unresolved-lines, unreviewed-scene-discontinuity |
| e21_a1 | 否 | 43/75 | 32 | unresolved-lines, unreviewed-scene-discontinuity |
| e21_a2 | 否 | 52/97 | 45 | unresolved-lines, unreviewed-scene-discontinuity |
| e21_a3 | 否 | 49/80 | 31 | unresolved-lines, unreviewed-scene-discontinuity |
| e22_a1 | 否 | 33/63 | 30 | unresolved-lines, unreviewed-scene-discontinuity |
| e22_a2 | 否 | 78/130 | 52 | unresolved-lines, unreviewed-scene-discontinuity |
| e22_a3 | 否 | 44/97 | 53 | unresolved-lines |
| e23_a1 | 否 | 49/93 | 44 | unresolved-lines, unreviewed-scene-discontinuity |
| e23_a2 | 否 | 50/83 | 33 | unresolved-lines, unreviewed-scene-discontinuity |
| e23_a3 | 否 | 47/82 | 35 | unresolved-lines |
| e24_a1 | 否 | 50/112 | 62 | unresolved-lines, insufficient-anchor-evidence, unreviewed-scene-discontinuity |
| e24_a2 | 否 | 47/88 | 41 | unresolved-lines, unreviewed-scene-discontinuity |
| e24_a3 | 否 | 30/64 | 34 | unresolved-lines, unreviewed-scene-discontinuity |
| e25_a1 | 否 | 39/93 | 54 | unresolved-lines, insufficient-anchor-evidence, unreviewed-scene-discontinuity |
| e25_a2 | 否 | 45/95 | 50 | unresolved-lines, unreviewed-scene-discontinuity |
| e25_a3 | 否 | 31/76 | 45 | unresolved-lines, insufficient-anchor-evidence |
| e26_a1 | 否 | 53/116 | 63 | unresolved-lines, unreviewed-scene-discontinuity |
| e26_a2 | 否 | 35/91 | 56 | unresolved-lines, insufficient-anchor-evidence, unreviewed-scene-discontinuity |
| e26_a3 | 否 | 30/76 | 46 | unresolved-lines, insufficient-anchor-evidence, unreviewed-scene-discontinuity |

## 复现

```bash
python tools/batch-calibrate.py --start 3 --end 26
python tools/batch-calibrate.py --start 3 --end 26 --align-only
python tools/apply-calibration.py
python tools/apply-calibration.py --apply
```

默认只生成候选；apply 明确执行后才更新主数据并保存原数据备份。
识别按音频SHA-256缓存；应用前核对音频、文本、算法SHA-256、时间边界和单调顺序。
