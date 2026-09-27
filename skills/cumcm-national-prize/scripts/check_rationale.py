# -*- coding: utf-8 -*-
"""check_rationale.py — 参数依据筛查脚本

扫描论文源文件（Typst/LaTeX/纯文本），找出所有"参数赋值/取值/范围"，
检查每个赋值附近是否有"依据句"（含因果/依据关键词）。
有赋值但附近无依据 → 标记"疑似缺依据"，供人工复核补写。

用法：
    python check_rationale.py <论文源文件路径>

说明：本脚本是"半自动筛漏"工具，用于快速定位"甩参数不讲依据"的位置，
不能替代对"依据是否合理"的语义判断——筛出的每一项仍需人工确认依据强度。
"""
import re
import sys

# 依据关键词（出现即认为该参数附近有依据表述）
RATIONALE_WORDS = [
    '因为', '由于', '依据', '取自', '为保证', '对应', '体现', '符合',
    '意味着', '选择', '使得', '以便', '源于', '基于', '根据', '故',
    '原因是', '考虑', '参照', '按', '按题意', '题目规定', '题目要求',
    '足以', '须', '兼顾', '均衡', '覆盖', '临界', '平衡', '上限',
    '自然', '探针', '退化', '滑动', '足够', '充分', '远大于', '不宜过大',
    '约束', '覆盖了', '隐含', '题面',
]

# 参数赋值/取值/范围的模式
ASSIGN_PATTERNS = [
    # 形如 N=30, M=10000, c1=2.0, R_max=8, mip_rel_gap=10^(-6)
    (re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)'), '赋值'),
    # 形如 从 0.5 到 2.0 / 从 0.9 线性递减至 0.4
    (re.compile(r'(从|由)\s*(-?\d+(?:\.\d+)?)\s*(到|至|递减至|增至)\s*(-?\d+(?:\.\d+)?)'), '范围'),
    # 形如 取 10000 / 取值 10000
    (re.compile(r'(取|取值|设为|设置为)\s*(-?\d+(?:\.\d+)?)'), '取值'),
]

# 疑似"甩参数"的裸赋值（常见于参数表/正文直接列数值）
BARE_ASSIGN = re.compile(r'(N|M|R_max|c\d*|omega|α|alpha|epsilon|ε)\s*=\s*\d+(?:\.\d+)?')


def has_rationale(segment):
    return any(w in segment for w in RATIONALE_WORDS)


def main(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')

    findings = []
    checked = 0
    for i, line in enumerate(lines, 1):
        # 跳过纯表格行（含 | 分隔符的三线表内容）和注释
        if line.strip().startswith('//'):
            continue
        for pat, kind in ASSIGN_PATTERNS:
            for m in pat.finditer(line):
                # 参数名或数值
                seg_start = max(0, m.start() - 60)
                seg_end = min(len(line), m.end() + 60)
                segment = line[seg_start:seg_end]
                if not has_rationale(segment):
                    # 取参数标识
                    param = m.group(1) if m.group(1) else m.group(0)[:20]
                    findings.append((i, kind, param, m.group(0), line.strip()[:50]))
                checked += 1

    print('=' * 64)
    print(f'参数依据筛查报告：共 {checked} 处赋值/取值/范围，{len(findings)} 处疑似缺依据')
    print('=' * 64)
    for i, kind, param, raw, ctx in findings:
        print(f'  [第{i}行] {kind} "{raw}" 附近 60 字内无依据词')
        print(f'           上下文: {ctx}')
    print('=' * 64)
    if findings:
        print('处理建议：逐项补"为什么这么取"的依据句，依据强度 ≥ 逻辑层')
        print('（"题目没给/我觉得好"= 空泛档 = 不合格）')
    else:
        print('全部参数附近均有依据表述（仍需人工复核依据强度）')
    return findings


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python check_rationale.py <论文源文件路径>')
        sys.exit(1)
    main(sys.argv[1])
