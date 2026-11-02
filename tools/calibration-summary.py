"""Render a human-readable batch status report from machine reports."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'diagnostics' / 'batch' / 'summary.json'
summary = json.loads(source.read_text(encoding='utf-8'))
acts = summary['acts']
ready = [a for a in acts if a['eligible']]
review = [a for a in acts if not a['eligible']]
receipt_path = ROOT / 'diagnostics' / 'batch' / 'application-receipt.json'
receipt = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else None
lines = ['# 第3–26集批量时间校准报告', '',
         f"实际已应用：{len(receipt['appliedActs']) if receipt else 0} 幕（以 application-receipt.json 为准）。", '',
         '这是机器辅助校准，不是逐句人工听校。音频在本机识别，没有上传。', '',
         f'- 已生成对齐报告：{len(acts)} / 72 幕',
         f'- 通过当前自动应用门槛：{len(ready)} 幕',
         f'- 保留原轴、需进一步复核：{len(review)} 幕',
         f'- 处理错误：{len(summary["errors"])}', '',
         '通过门槛的候选仍可能含短句偏移估计，逐句 timingNeedsReview 标记和来源保留。',
         '未通过的幕不混合新旧时间轴、不盲目跨过场插值；识别缓存可用于后续精校。', '',
         '| 幕 | 自动应用候选 | 可靠锚点/句数 | 待复核句 | 阻断原因 |',
         '|---|---|---:|---:|---|']
for act in acts:
    reason = ', '.join(act.get('blockedReasons', [])) or ('—' if act['eligible'] else '见逐幕报告')
    lines.append(f"| {act['key']} | {'是' if act['eligible'] else '否'} | {act['anchorCount']}/{act['lineCount']} | {act['reviewCount']} | {reason} |")
if summary['errors']:
    lines += ['', '## 处理错误', ''] + [f"- {item['key']}: {item['error']}" for item in summary['errors']]
lines += ['', '## 复现', '', '```bash',
          'python tools/batch-calibrate.py --start 3 --end 26',
          'python tools/batch-calibrate.py --start 3 --end 26 --align-only',
          'python tools/apply-calibration.py',
          'python tools/apply-calibration.py --apply',
          '```', '',
          '默认只生成候选；apply 明确执行后才更新主数据并保存原数据备份。',
          '识别按音频SHA-256缓存；应用前核对音频、文本、算法SHA-256、时间边界和单调顺序。']
(ROOT / 'diagnostics' / 'batch-calibration-report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Reports', len(acts), 'ready', len(ready), 'review', len(review), 'errors', len(summary['errors']))
