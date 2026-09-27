"""PDF验证脚本——检查编译后的PDF：图片嵌入 + 正文页数 + 文件体积。

官方口径（《全国大学生数学建模竞赛论文格式规范》2026年修订稿）：
  · 第三条：摘要页（第 3 页）从此页开始编页码，页脚中部，阿拉伯数字从"1"连续编号
  · 第四条：正文从第 4 页开始（不要目录），不超过 30 页；正文之后是附录（页数不限）
  · 第十条：电子版论文为单个文件，不超过 20MB

计数口径说明：声明的 30 页上限只约束"正文"，**摘要页与附录都不计入**。
本脚本以「首个页首出现'附录'的页」为界，其前的页数减去 1 页摘要页即为正文页数。
"""
import sys, re, os, pymupdf

BODY_LIMIT = 30      # 官方正文上限（页）
SIZE_LIMIT_MB = 20   # 官方电子版体积上限（MB）


def find_appendix_page(doc):
    """定位附录起始页（搜索页首"附录"字样），返回 0 基页码；找不到返回总页数。"""
    for i in range(doc.page_count):
        text = doc[i].get_text()
        if re.search(r'^\s*附录', text, re.M):
            return i
    return doc.page_count


def check(pdf_path):
    if not os.path.exists(pdf_path):
        print(f'文件不存在：{pdf_path}')
        print('用法：python pdf_check.py <pdf路径>')
        sys.exit(2)

    doc = pymupdf.open(pdf_path)
    total = doc.page_count
    images = sum(len(doc[i].get_images()) for i in range(total))
    app = find_appendix_page(doc)
    body_pages = max(app - 1, 0)   # 去掉摘要页；附录不计入
    doc.close()
    size_mb = os.path.getsize(pdf_path) / 1024 / 1024

    issues = []
    if images == 0:
        issues.append('No embedded images')
    if body_pages > BODY_LIMIT:
        issues.append(f'正文约 {body_pages} 页，超过官方上限 {BODY_LIMIT} 页（摘要页与附录不计）')
    if body_pages < 10:
        issues.append(f'正文仅 {body_pages} 页，内容可能单薄（非官方判据，供参考）')
    if size_mb > SIZE_LIMIT_MB:
        issues.append(f'文件体积 {size_mb:.1f}MB，超过官方 {SIZE_LIMIT_MB}MB 上限')

    print(f'总页数={total}, 正文约={body_pages} 页, 附录={total - app} 页, 图片={images}, 体积={size_mb:.1f}MB')
    if issues:
        print('ISSUES:', '; '.join(issues))
        sys.exit(1)
    print('OK')


if __name__ == '__main__':
    check(sys.argv[1] if len(sys.argv) > 1 else 'paper/output.pdf')
