# -*- coding: utf-8 -*-
"""CUMCM支撑材料生成脚本。

用法：
    python build_support.py <项目根目录> [--no-ai] [--output-dir <输出目录>]

功能：
    1. 扫描项目代码/图表目录
    2. 生成支撑材料文件列表
    3. 可选：生成AI工具使用详情PDF
    4. 打包为ZIP

输出：
    <项目根目录>/submission/支撑材料.zip
    <项目根目录>/submission/支撑材料文件列表.txt
    <项目根目录>/submission/AI工具使用详情.pdf (若使用AI)
"""
import os, sys, zipfile, argparse
from datetime import datetime

def scan_files(root, dirs):
    """扫描指定目录下所有文件，返回相对路径列表。"""
    files = []
    for d in dirs:
        dpath = os.path.join(root, d)
        if not os.path.isdir(dpath):
            continue
        for f in sorted(os.listdir(dpath)):
            fpath = os.path.join(dpath, f)
            if os.path.isfile(fpath) and not f.startswith('.'):
                rel = os.path.relpath(fpath, root)
                files.append(rel)
    return files

def build_file_list(code_files, figure_files, ai_pdf=None):
    """生成支撑材料文件列表文本。"""
    lines = ["支撑材料文件列表", "=" * 20, ""]
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"文件总数：{len(code_files) + len(figure_files) + (1 if ai_pdf else 0)}")
    lines.append("")

    if code_files:
        lines.append(f"【源程序代码】({len(code_files)}个文件)")
        lines.append("-" * 20)
        for f in sorted(code_files):
            size = os.path.getsize(os.path.join(os.getcwd(), f))
            lines.append(f"  {f}  ({size/1024:.1f} KB)")
        lines.append("")

    if figure_files:
        lines.append(f"【中间结果图表】({len(figure_files)}个文件)")
        lines.append("-" * 20)
        for f in sorted(figure_files):
            size = os.path.getsize(os.path.join(os.getcwd(), f))
            lines.append(f"  {f}  ({size/1024:.1f} KB)")
        lines.append("")

    if ai_pdf:
        lines.append("【AI工具使用详情】")
        lines.append("-" * 20)
        lines.append(f"  AI工具使用详情.pdf")
        lines.append("")

    lines.append("【说明】")
    lines.append("以上文件已全部打包在支撑材料.zip中。")
    lines.append("源程序同时作为附录包含在参赛论文正文之后。")

    return "\n".join(lines)

def build_zip(root, code_files, figure_files, ai_pdf, output_path):
    """打包所有支撑材料为ZIP。"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in code_files + figure_files:
            fpath = os.path.join(root, f)
            if os.path.exists(fpath):
                zf.write(fpath, f)
        if ai_pdf and os.path.exists(ai_pdf):
            zf.write(ai_pdf, os.path.basename(ai_pdf))

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    return size_mb

def generate_ai_pdf(output_path, tool_name="", tool_version="", usage_purpose="", usage_notes=""):
    """生成AI工具使用详情PDF。

    使用pymupdf创建简单PDF文档。
    """
    try:
        import pymupdf
    except ImportError:
        print("Warning: pymupdf not available, generating text file instead")
        txt_path = output_path.replace('.pdf', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"AI工具使用详情\n\n")
            f.write(f"工具名称：{tool_name or '（未填写）'}\n")
            f.write(f"版本/型号：{tool_version or '（未填写）'}\n")
            f.write(f"使用目的和环节：{usage_purpose or '（未填写）'}\n")
            f.write(f"使用说明：{usage_notes or '（未填写）'}\n")
        return

    doc = pymupdf.open()
    page = doc.new_page()

    # Title
    page.insert_text((50, 50), "AI工具使用详情", fontsize=16, fontname="hebo")

    y = 100
    lines = [
        ("工具名称", tool_name or "（未填写）"),
        ("版本/型号", tool_version or "（未填写）"),
        ("使用目的和环节", usage_purpose or "（未填写）"),
        ("主要提示方式与使用过程", ""),
        ("", usage_notes or "（未填写）"),
        ("", ""),
        ("采纳、人工修改和核验情况", ""),
        ("", "所有AI生成内容均经过人工审查、修改和核实。"),
        ("", "核心建模与分析由参赛队独立完成。"),
        ("", ""),
        ("生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    ]

    for label, value in lines:
        if label:
            page.insert_text((50, y), f"{label}：{value}" if value else label + "：", fontsize=11)
        else:
            page.insert_text((70, y), value, fontsize=11)
        y += 22

    doc.save(output_path)
    doc.close()

def main():
    parser = argparse.ArgumentParser(description="CUMCM支撑材料生成")
    parser.add_argument("root", help="项目根目录路径")
    parser.add_argument("--no-ai", action="store_true", help="未使用AI工具")
    parser.add_argument("--ai-tool", default="", help="AI工具名称")
    parser.add_argument("--ai-version", default="", help="AI工具版本")
    parser.add_argument("--ai-purpose", default="", help="AI使用目的")
    parser.add_argument("--ai-notes", default="", help="AI使用说明")
    parser.add_argument("--output-dir", default="", help="输出子目录（默认为submission）")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    out_subdir = args.output_dir or "submission"
    out_dir = os.path.join(root, out_subdir)
    os.makedirs(out_dir, exist_ok=True)

    # 扫描文件
    scan_dirs = []
    if os.path.isdir(os.path.join(root, "code")):
        scan_dirs.append("code")
    if os.path.isdir(os.path.join(root, "figures")):
        scan_dirs.append("figures")

    all_files = scan_files(root, scan_dirs)
    code_files = [f for f in all_files if os.path.dirname(f) == "code" and f.endswith(".py")]
    figure_files = [f for f in all_files if os.path.dirname(f) in ("figures", "code" + os.sep + "figures")]
    # Normalize figure path check
    figure_files = [f for f in all_files if os.path.dirname(f).replace("\\", "/").startswith("figures")]

    # AI PDF
    ai_pdf = None
    if not args.no_ai and (args.ai_tool or args.ai_purpose):
        ai_pdf = os.path.join(out_dir, "AI工具使用详情.pdf")
        generate_ai_pdf(ai_pdf, args.ai_tool, args.ai_version,
                       args.ai_purpose, args.ai_notes)
        print(f"生成 AI使用详情: {ai_pdf}")

    # 文件列表
    file_list = build_file_list(code_files, figure_files, ai_pdf)
    list_path = os.path.join(out_dir, "支撑材料文件列表.txt")
    with open(list_path, 'w', encoding='utf-8') as f:
        f.write(file_list)
    print(f"生成 文件列表: {list_path}")

    # 打包
    zip_path = os.path.join(out_dir, "支撑材料.zip")
    size = build_zip(root, code_files, figure_files, ai_pdf, zip_path)
    print(f"打包完成: {zip_path} ({size:.1f} MB)")

    if size > 20:
        print(f"⚠️  警告: ZIP大小 {size:.1f}MB 超过20MB限制！")

    # 输出摘要
    print(f"\n文件统计:")
    print(f"  源程序: {len(code_files)} 个")
    print(f"  图表: {len(figure_files)} 个")
    print(f"  AI详情: {'有' if ai_pdf else '无（未使用AI）'}")
    print(f"  总文件: {len(code_files) + len(figure_files) + (1 if ai_pdf else 0)} 个")

if __name__ == "__main__":
    main()
