# 运行时环境与工具调用完全指南

> 本文档是 skill 的"操作系统手册"——新对话窗口不需要上下文，读完本文档就能找到所有依赖、知道所有命令怎么写。
> 每次开始新任务时，先扫描本文档确认环境可用。

---

## 1. Python 运行时

### 1.1 Python 解释器

用你环境里的 Python 3.10+ 即可（下文统一写作 `python`）：

```bash
python --version
```

### 1.2 Python 包安装（建议用虚拟环境，避免污染系统环境）

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt
# macOS / Linux
.venv/bin/pip install -r requirements.txt
```

**运行脚本时用**：`.venv\Scripts\python script.py`（Windows）或 `.venv/bin/python script.py`。

### 1.3 关键依赖

| 包 | 用途 | 验证命令 |
|----|------|----------|
| typst | Typst 编译（推荐，支持三线表函数语法） | `python -c "import typst; print(typst.__version__)"` |
| pymupdf | PDF 页数检查、图片嵌入验证、PDF→PNG 渲染 | `python -c "import pymupdf; doc=pymupdf.open('t.pdf'); print(doc.page_count)"` |
| python-docx | DOCX 文件生成与读取 | `python -c "import docx; print(docx.__version__)"` |
| pandas | 数据处理（`audit_numbers.py` 依赖） | `python -c "import pandas; print(pandas.__version__)"` |
| numpy | 数值计算 | `python -c "import numpy; print(numpy.__version__)"` |
| scikit-learn | 机器学习/逻辑回归/交叉验证 | `python -c "import sklearn; print(sklearn.__version__)"` |
| matplotlib | 图表生成 | `python -c "import matplotlib; print(matplotlib.__version__)"` |

---

## 2. Typst 编译

### 2.1 两种编译方式对比

| | npx typst | Python typst |
|------|------|------|
| 命令 | `npx -y typst compile` | `python -c "import typst; typst.compile(...)"` |
| table.hline 支持 | ❌ 不支持（旧版本） | ✅ 支持 |
| 函数式 stroke | ❌ 不支持 | ✅ 支持 |
| PDF 矢量图嵌入 | ✅ 支持 | ❌ 不嵌入 PDF（需先转 PNG） |
| PNG 图嵌入 | ✅ 支持 | ✅ 支持 |
| 推荐用途 | 快速编译简单文档 | **论文编译（使用三线表函数）** |

### 2.2 Python typst 编译（推荐，论文用）

```bash
cd "{PROJECT_ROOT}"
python -c "
import typst
pdf = typst.compile('paper_typst/main.typ', root='.')
with open('paper/output.pdf', 'wb') as f:
    f.write(pdf)
print('compiled, size:', len(pdf))
"
```

**注意**：root 参数必须设为项目根目录，Typst 源文件中引用的相对路径（如图片 `figures_png/xxx.png`）相对于 root 解析。

### 2.3 npx typst 编译（备用，简单文档）

```bash
npx -y typst compile --root . paper_typst/main.typ paper/output.pdf
```

**注意**：若 Typst 源文件使用了三线表函数（`stroke: (x, y) => {...}`），旧版 npx typst 会失败，此时必须用 Python typst。

---

## 3. SKILL 内部文件路径（相对于 skill 根目录）

| 文件 | 路径 | 读取命令 |
|------|------|----------|
| SKILL.md | 当前文件 | 加载 skill 时自动注入 |
| 写作模板（唯一） | `references/paper_skeleton.md` | `Read` + 相对路径 |
| 排版头（最终修正版） | `references/typst_setup.md` | `Read` + 相对路径 |
| 故障排查 | `references/troubleshooting.md` | `Read` + 相对路径 |
| 代码模板 | `references/code_templates.md` | `Read` + 相对路径 |
| 运行时指南 | `references/tool_locations.md` | `Read` + 相对路径（本文档） |
| 核验脚本 | `scripts/audit_numbers.py` / `audit_docx.py` / `pdf_check.py` / `font_check.py` / `check_rationale.py` | 直接运行 |
| 参考论文 Typst | `examples/信用卡评分_参考论文.typ` | `Read` 查看源码（学结构与写法；排版要素以 `typst_setup.md` 为准） |
| 参考论文 PDF | `examples/信用卡评分_参考论文.pdf` | 直接打开查看（22 页） |
| Typst 模板 | `templates/typst-cumcm.zip`（第三方上游模板） | 仅供查目录结构；**排版一律用 `typst_setup.md` 的修正版排版头**，勿直接套原始模板 |
| LaTeX 模板 | `templates/latex-cumcm.zip`（第三方上游模板） | 同上 |

---

## 4. 项目工作目录结构（参考）

一份完整论文项目的推荐目录结构（路径自定，勿照抄）：

```
{PROJECT_ROOT}/
├── code/            建模 Python 脚本（01_eda.py, 03_modeling.py 等）
├── figures/         原始 PDF 矢量图表
├── figures_png/     转换后的 300DPI PNG 图表（编译用这个）
├── paper/           论文 PDF
├── paper_typst/     Typst 源文件（main.typ）
├── results/         建模结果 CSV（数值溯源的唯一真源）
└── .cache/          临时文件（PDF 截图、解压的模板等）
```

---

## 5. 外部工具

| 工具 | 调用方式 | 用途 |
|------|------|------|
| draw.io | `https://app.diagrams.net`（在线） | 画技术路线图/流程图 |
| Inkscape | 官网下载安装 | 图表最终润色（统一字体/配色/标注） |
| Visio | 微软 Office 套件 | 流程图备选 |
| Git Bash | 系统自带 / 随客户端安装 | 命令行操作 |

---

## 6. 桌面和下载路径

正文中引用路径时使用你本机的实际路径（Windows 默认：`%USERPROFILE%\Desktop`、`%USERPROFILE%\Downloads`）。

---

## 7. 常用自动化命令

### 7.1 PDF 逐页截图（视觉检查）

```bash
cd "{PROJECT_ROOT}"
python -c "
import pymupdf, os
os.makedirs('.cache/pages', exist_ok=True)
doc = pymupdf.open('paper/output.pdf')
for i, p in enumerate(doc):
    p.get_pixmap(dpi=120).save(f'.cache/pages/p{i+1:02d}.png')
print(f'{doc.page_count} pages rendered')
doc.close()
"
```

### 7.2 论文自动化检查

**检查脚本位置**：`scripts/` 下的核验脚本（见第 3 节表格）。
**功能**：页数/体积、字体降级、数值溯源、docx 结构、无依据参数。

### 7.3 PDF 图片嵌入验证

```bash
cd "{PROJECT_ROOT}"
python -c "
import pymupdf
doc = pymupdf.open('paper/output.pdf')
total = sum(len(doc[i].get_images()) for i in range(doc.page_count))
print(f'{doc.page_count} pages, {total} embedded images')
doc.close()
"
```

### 7.4 图表批量 PDF→PNG 转换（300DPI）

Python typst **不嵌入 PDF 矢量图**，编译前必须把图转成 PNG：

```bash
cd "{PROJECT_ROOT}"
python -c "
import pymupdf, os
os.makedirs('figures_png', exist_ok=True)
for f in os.listdir('figures'):
    if f.endswith('.pdf'):
        doc = pymupdf.open(f'figures/{f}')
        doc[0].get_pixmap(dpi=300).save(f'figures_png/{f[:-4]}.png')
        doc.close()
print('done')
"
```

### 7.5 matplotlib 论文级全局配置

在绘图脚本开头添加：

```python
import matplotlib
matplotlib.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'font.sans-serif': ['SimHei', 'Microsoft YaHei'],
    'axes.unicode_minus': False,
    'axes.grid': True,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'lines.linewidth': 2.0,
})

# Okabe-Ito 色盲友好色板
from cycler import cycler
matplotlib.rcParams['axes.prop_cycle'] = cycler(color=[
    '#009E73', '#56B4E9', '#E69F00', '#0072B2', '#D55E00', '#CC79A7'
])
```

**保存图表时**：
```python
for s in ['top', 'right']:
    ax.spines[s].set_visible(False)  # 去掉上边框和右边框
fig.tight_layout()
fig.savefig('output.png', dpi=300, bbox_inches='tight')
```
