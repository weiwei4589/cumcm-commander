# Typst / LaTeX 编译故障排查指南

> 记录在国赛论文实战中实际遇到的编译问题及解决方案。

## 目录

- [Typst 常见故障](#typst-常见故障)
- [LaTeX 常见故障](#latex-常见故障)
- [网络/下载问题](#网络下载问题)
- [PDF 视觉检查](#pdf-视觉检查)

---

## Typst 常见故障

### 1. `table.hline` 不存在

**症状**：`error: function table does not contain field hline`

**原因**：Typst v0.10.0 及更早版本不支持 `table.hline()`。该函数在 v0.11.0 才引入。

**解决**：选择以下任一方案：
- 方案A（推荐）：使用 Python typst 模块 `pip install typst`（内置高版本编译器）
- 方案B：升级 Typst CLI 到 v0.11.0+
- 方案C：用三线表替代方案——将表头和数据分两个 table，中间用 `line()` 分隔

**Python typst 编译命令**：
```python
import typst
pdf = typst.compile('main.typ', root='.')
with open('output.pdf', 'wb') as f:
    f.write(pdf)
```

### 2. `stroke` 不支持函数参数

**症状**：`error: expected length, color, or none, found function`

**原因**：Typst v0.10.0 的 `table(stroke: ...)` 不接受函数式 `(x, y) => {...}` 语法。

**解决**：三线表改用以下方案：
```typst
#let 三线表(columns: auto, ..body, caption: none) = {
  let rows = body.pos()
  let ncols = if type(columns) == int { columns } else { columns.len() }
  let nrows = calc.floor(rows.len() / ncols)
  figure(
    table(
      columns: columns,
      stroke: (x, y) => {
        if y == 0 { (top: 1.5pt, bottom: 0.75pt) }
        else if y == nrows - 1 { (bottom: 1.5pt) }
        else { none }
      },
      ..rows
    ),
    caption: caption
  )
}
```
此语法在 Python typst v0.15.0+ 和 Typst CLI v0.11.0+ 均支持。

### 3. 图表题注双重标签（"图 1 图 1"两个编号）

**症状**：PDF 显示 "Figure 1: 图 1-1 ..."（英文前缀），或更隐蔽的 **"图 1　图 1 技术路线图"**（中文自动编号 + 手写编号叠在一起）。

**原因**：Typst 的 `figure` 默认自动给 caption 加编号，而 caption 里又手写了"图 1 xxx"，两者叠加成两个"图 1"。

**解决（两种，选其一）**：
- 方案A（推荐，caption 里已手写"图 N"编号时）：直接关掉自动编号
  ```typst
  #set figure(numbering: none)
  ```
- 方案B（想用自动编号）：caption 里**不写**编号，只写说明文字，让 Typst 自动编号；并用 `#set text(lang: "zh")` + `#show figure.caption: it => it.body` 去掉英文前缀。

**连带规则**：绘图脚本里的 `ax.set_title('图9 某某')` **不能带"图X"编号**——编号只属于论文题注，不属于图内。图内标题只写描述（如 `ax.set_title('专家权重集中度对总满意度的影响')`），否则"图内印的编号"和"题注编号"又会撞车、错位。

### 4. 数学标识符需要引号

**症状**：`WOE_i` 被解析为标签

**原因**：多字母标识符在 Typst 中必须用引号包裹。

**解决**：使用 `$"WOE"_i$` 而非 `$WOE_i$`

### 5. 表格数据行末尾多余逗号

**症状**：`error: unexpected comma` 在表格最后一行

**原因**：Typst 对表格最后的逗号敏感，三线表函数拼接时可能产生连续逗号。

**解决**：确保每个 `#三线表(...)` 调用中，数据行末尾无多余逗号。

### 6. 表格左对齐，`align` 居中不生效

**症状**：表格左对齐，只有表题居中；尤其窄表明显偏左。

**原因**：Typst 的 `table` 盒模型默认撑满 100% 行宽，`align(center, table(...))` 和 `align(center)[#table(...)]` 都**不生效**（table 撑满后没有可居中的空间）。之前容易被"恰好撑满内容区的宽表"蒙蔽——那种表左对齐=居中，窄表才暴露问题。

**解决**：唯一可靠的方式是用 `figure(table(...))` 包裹——`figure` 默认收缩到内容宽度并居中：
```typst
#let threeline(cols, header, ..body) = {
  figure(
    table(
      columns: cols,
      stroke: none,
      align: (center,) * cols.len(),
      table.hline(stroke: 1.5pt),
      table.header(..header),
      table.hline(stroke: 0.75pt),
      ..body,
      table.hline(stroke: 1.5pt),
    ),
  )
}
```

### 7. 正文段落顶格（首行缩进丢失）——三种成因，逐一排查

**症状**：正文段落顶格、无首行缩进；或只有部分段落（标题后/公式后/图表后的第一段）顶格。

**成因与解法（三种，实战全部踩过）**：

- **成因A：`#show par` 规则破坏缩进**。`#show par: it => block(above: 6pt, below: 6pt, it)` 会重新包装每个段落，顺带破坏 `first-line-indent`。
  解法：删除这条 `#show par` 规则。官方规范本就是「段首空两格 + 段间无空行」；确需调整密度用 `#set par(leading: ...)` 调行距。

- **成因B：Typst 默认"块级元素后的第一个段落不缩进"**。标题（heading）、展示公式（display equation）、图表（figure）后面的第一个段落被视为"新内容的开始"而顶格——这是最隐蔽的一类，散布全文。
  解法：在三类块级元素后各塞一个不可见空 box，打断"块→段落"紧邻关系（已实测，公式编号不受影响）：
  ```typst
  #show heading: it => { it; box() }
  #show math.equation: it => { it; box() }
  #show figure: it => { it; box() }
  ```
  **注意三条都要加**——只加 heading 漏公式后顶格，只加前两条漏图表后顶格（图表后紧跟的分析段是最常见残留）。

- **成因C：验证时只查标题行没查正文段**。只抽标题附近的行检查，会漏掉全文散布的顶格段。
  解法：程序化扫**全部正文段落的首行** x 坐标，输出逐段缩进清单，逐段核对（禁止只抽一个"看起来对"的样本）。

### 8. 摘要/参考文献/附录被自动编号，正文整体 +1 错位

**症状**：摘要显示成「1. 摘 要」，正文从「2. 问题重述」开始，全部章节编号 +1 错位。

**原因**：摘要用了 `=` 一级标题，被 `#set heading(numbering: "1.")` 自动编号。

**解决**：摘要、参考文献、附录都是**非正文章节**，不用 `=` 标题，改用不参与 numbering 的自定义标题：
```typst
#align(center)[#text(size: 16pt, font: "SimHei", weight: "bold")[摘 要]]
```

### 9. 段间距加了没生效，或加了破坏缩进

**症状**：想给段落加间距，`set` 形式对 par 不生效，`show` 形式又破坏缩进。

**解决**：数模论文官方规范本就是「段间无空行」，**不要加段间距**。段落的"呼吸感"来自 1.5 倍行距 + 首行缩进，不是段间空行。图表与正文的留白用 `#set block(above/below)` 或 figure 的 `gap` 处理，不用动段落本身。

---

## LaTeX 常见故障

### 1. xelatex 找不到中文字体

**症状**：`! LaTeX Error: File 'SimSun.ttf' not found`

**解决**：
- Windows：安装"微软雅黑"或"宋体"系统字体
- Mac：安装"华文宋体"
- Linux：`apt install fonts-wqy-zenhei`

### 2. MiKTeX 自动安装包失败

**症状**：`MiKTeX Package Manager` 弹窗无法安装缺失包

**原因**：仓库源连不上（如配置 127.0.0.1:8000 本地代理）。

**解决**：改为 TeX Live（推荐）或手动设置 MiKTeX 仓库源为镜像。

### 3. cumcmthesis.cls 缺少字体

**症状**：`! Font \zihao{-4}\heiti not found`

**解决**：确保系统安装了黑体（SimHei）和宋体（SimSun），运行 `fc-list | grep -i sim` 检查。

---

## 网络/下载问题

### 1. GitHub 下载速度慢或超时

**解决**：
- 方案A：使用 `npx -y typst` 可直接使用 npm 镜像
- 方案B：从 gitee 镜像拉取（如 `gitee.com/mirrors/CUMCM-Thesis`）
- 方案C：手动下载 zip 后在本地编译

### 2. npm 安装 typst 失败

**解决**：
- 使用 `npx -y @myriaddreamin/typst.ts`（Typst 的 TypeScript 移植版）
- 或直接用 pip 安装：`pip install typst`

---

## PDF 视觉检查

### 1. 中文字体显示为方块

**解决**：检查 typst 编译时是否能找到系统字体。在 Windows 上通常自动识别 SimSun/SimHei。

### 2. 图片显示为空白或低分辨率

**解决**：确认图片路径正确。Typst 中路径相对于 main.typ：
```typst
image("../../figures/roc.png", width: 85%)
```

### 3. 三线表线粗细不对

**解决**：检查 `stroke` 参数。国赛标准：顶线 1.5pt、表头下线 0.75pt、底线 1.5pt。
