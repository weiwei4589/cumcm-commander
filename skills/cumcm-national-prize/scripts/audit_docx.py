# -*- coding: utf-8 -*-
"""docx 结构体检：检查格式转换残留的脏结构

检查项（有问题就返修）：
1. 分节符：段落内 <w:sectPr>（下一页分节符），会强制分页产生大块空白、页码重复
2. 公式形式：全是图片(<w:drawing>)且无原生公式(<m:oMath>)，是转换残留，易有乱码
3. 乱码字符：⑴(ω) į(i) ∨(∀) 等字体映射错乱
4. 空格残留：中文词语间混入空格（术语替换残留）

用法：python audit_docx.py <docx路径>
返回码：0=通过，1=发现问题需返修
"""
import zipfile, re, sys

def audit(path):
    z = zipfile.ZipFile(path)
    xml = z.read('word/document.xml').decode('utf-8')
    paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.S)
    issues = []    # FAIL：必须返修
    warns = []     # WARN：提示，需人工判断

    # 1. 分节符（段落内 sectPr，正常应 0 个；只允许 body 末尾的最后一个节设置）
    sect_in_para = sum(1 for p in paras if '<w:sectPr' in p)
    if sect_in_para > 0:
        issues.append(f'分节符 {sect_in_para} 个（应 0 个，多余分节符会强制分页、产生大块空白和页码重复）')

    # 2. 公式形式（提示，不强制——公式用图片还是原生公式不锁死）
    omath = xml.count('<m:oMath')
    drawing = xml.count('<w:drawing>')
    if omath == 0 and drawing > 0:
        warns.append(f'公式全是图片（{drawing} 张）无原生公式，常见于格式转换残留，建议人工确认公式无乱码')

    # 3. 乱码字符（字体映射错乱）
    for ch, name in [('⑴', 'ω(omega)'), ('į', '斜体i'), ('∨', '∀(全称量词)')]:
        n = xml.count(ch)
        if n > 0:
            issues.append(f'乱码字符 {ch}（应为{name}）{n} 处')

    # 4. 空格残留（中文词语间混入空格）
    full = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml, re.S))
    sp = re.findall(r'[\u4e00-\u9fff] +[\u4e00-\u9fff]', full)
    if sp:
        warns.append(f'中文词语间空格残留 {len(sp)} 处（需结合上下文判断，正文里的才是问题，代码字符串里的不算）')

    # 5. 正文首行缩进（正文叙述段应有 firstLine/firstLineChars，否则标题下正文顶格）
    no_indent = 0
    for p in paras:
        t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S)).strip()
        if not t or '黑体' in p or '微软雅黑' in p:
            continue
        if not re.search(r'[\u4e00-\u9fff]', t):
            continue
        if len(t) < 8:
            continue
        if re.match(r'^\s*(图|表)\s*\d', t):
            continue
        ind = re.search(r'<w:ind [^>]*>', p)
        if not ind or 'firstLine' not in ind.group(0):
            no_indent += 1
    if no_indent > 0:
        warns.append(f'正文段落无首行缩进 {no_indent} 个（标题下正文应缩进 2 字符，转换残留会破坏缩进）')

    # 6. 页码（实际被 sectPr 引用的页脚应是 PAGE 域自动页码，不能是死数字）
    # 从 document.xml 提取 footerReference 的 rId，经 rels 映射到 footer 文件，只查这些
    footer_rids = set(re.findall(r'<w:footerReference r:id="(rId\d+)"', xml))
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
    bad_page = []
    for rid in footer_rids:
        m = re.search(rid + r'"[^>]*Target="(footer\d+\.xml)"', rels)
        if not m:
            continue
        fn = 'word/' + m.group(1)
        c = z.read(fn).decode('utf-8')
        if 'PAGE' in c:
            continue  # 有 PAGE 域，正常
        txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', c, re.S))
        if txt.strip().isdigit():
            bad_page.append(txt.strip())
    if bad_page:
        issues.append(f'生效页脚页码是死数字（非 PAGE 域自动页码）：{bad_page}，会导致每页页码都显示同一个数')

    if warns:
        print('WARN（提示，需人工判断）：')
        for w in warns:
            print('  -', w)
    if issues:
        print('FAIL：发现结构问题，需返修：')
        for i in issues:
            print('  -', i)
        return 1
    print('PASS：docx 结构体检通过（无硬性问题' + ('，有提示项' if warns else '') + '）')
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法：python audit_docx.py <docx路径>')
        sys.exit(2)
    sys.exit(audit(sys.argv[1]))
