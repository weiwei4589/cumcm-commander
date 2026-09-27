"""字体校验脚本——确认 PDF 里的中文字形用的确实是排版标准要求的字体，而不是静默降级的替代字体。

为什么必须有这个脚本：
  Typst 在字体缺失时**不报错**，会静默换成系统里的其他字体（实测：指定 SimSun 却渲染成 KaiTi）。
  编译"成功"不等于排版"正确"——字体一旦静默降级，字形、字距、整体观感都会偏离国赛标准，
  而 PDF 打开看又"像是对的一样"。本脚本把这个隐性问题变成显性检查。

判断方式（精确到字形，不做"有没有别的字体"这种粗判）：
  逐段扫描 PDF 文本，凡是含中日韩字符（CJK）的文本段，检查其字体是否在标准中文清单内。
  西文/数学/代码字体（Times、Libertinus、DejaVu、NewCMMath 等）不参与判定——
  它们在论文中正常存在，不影响排版合规。

标准中文清单（= references/typst_setup.md 的用户标准，只有两个）：
  正文 SimSun（宋体） / 标题 SimHei（黑体）

用法：
  python font_check.py <pdf路径>
  退出码 0 = 中文字体正确；1 = 中文字形发生降级；2 = 参数或文件错误
"""
import sys, os, re
import pymupdf

# skill 排版标准「声明」的中文字体（对应 references/typst_setup.md，仅此两个）：
#   正文 font: ("SimSun", "Times New Roman")  → SimSun
#   标题 #show heading: set text(font: "SimHei") → SimHei
DECLARED_CJK = ['simsun', 'simhei']

# 属合法中文字体但未被 skill 声明——出现即说明没按标准字体走，需人工确认
OTHER_CJK = ['nsimsun', 'simkai', 'kaiti', 'fangsong', 'simfang', 'songti', 'heiti',
             'stsong', 'stkaiti', 'sthei', 'microsoftyahei', 'yahei', 'pingfang']

CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef]')


def bare(n):
    """去掉 PDF 内嵌字体的子集前缀，如 GYXKYP+SimSun → SimSun"""
    return re.sub(r'^[A-Z]{6}\+', '', (n or '').strip())


def check(pdf_path):
    if not os.path.exists(pdf_path):
        print(f'文件不存在：{pdf_path}')
        print('用法：python font_check.py <pdf路径>')
        sys.exit(2)

    doc = pymupdf.open(pdf_path)
    cjk_fonts = {}      # 承载中文字形的字体 → 命中字符数
    sample = {}
    for pg in doc:
        for blk in pg.get_text('dict')['blocks']:
            for line in blk.get('lines', []):
                for span in line['spans']:
                    txt = span.get('text', '')
                    if not CJK_RE.search(txt):
                        continue
                    fname = bare(span.get('font', ''))
                    cjk_fonts[fname] = cjk_fonts.get(fname, 0) + len(txt)
                    sample.setdefault(fname, txt.strip()[:24])
    doc.close()

    print(f'承载中文字形的字体共 {len(cjk_fonts)} 种（标准声明：SimSun 正文 / SimHei 标题）：')
    for n, cnt in sorted(cjk_fonts.items(), key=lambda x: -x[1]):
        low = n.lower().replace(' ', '')
        if any(s in low for s in DECLARED_CJK):
            mark = '✓ 符合声明'
        elif any(s in low for s in OTHER_CJK):
            mark = '⚠ 未声明'
        else:
            mark = '✗ 非中文字体'
        print(f'  [{mark}] {n}  ({cnt} 字符)  例：{sample.get(n, "")}')

    issues = []
    if not cjk_fonts:
        issues.append('未检出任一中文字形——若论文含中文，说明字体未嵌入或检测口径异常')
    for n, cnt in cjk_fonts.items():
        low = n.lower().replace(' ', '')
        if any(s in low for s in DECLARED_CJK):
            continue
        if any(s in low for s in OTHER_CJK):
            issues.append(f'中文字体未按标准声明："{n}" 承担了 {cnt} 个中文字符，'
                          f'标准要求正文 SimSun / 标题 SimHei')
        else:
            issues.append(f'中文字形由非中文字体渲染："{n}"（{cnt} 字符）——疑似严重降级或字体缺失')

    if issues:
        print('ISSUES:')
        for i in issues:
            print(f'  - {i}')
        print('提示：字体缺失时 Typst 会静默替换而不报错。请在编译环境安装标准中文字体（宋体/黑体），'
              '或核对 typst_setup.md 的 font 拼写：正文 ("SimSun", "Times New Roman")、标题 "SimHei"。')
        sys.exit(1)

    print('OK：中文字形符合排版标准，未发现静默降级。')


if __name__ == '__main__':
    check(sys.argv[1] if len(sys.argv) > 1 else 'paper/output.pdf')
