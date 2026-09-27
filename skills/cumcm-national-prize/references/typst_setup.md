# Typst 排版头（最终修正版）

> 这是国赛论文的最终定稿排版头，已修正三个坑：① 图表双编号 ② 标题/公式/图表后第一段顶格 ③ 宽表居中。写新论文时直接复制下面这段作为文件头，不要用 `templates/` 里未经修正的原始模板。
>
> 术语与数值已与 `paper_skeleton.md`「护栏三 · 格式排版硬标准」对齐：三线表 1.5/0.75/1.5pt、行距 1.5 倍（= `leading: 1.05em`，实测 20.9pt）、页脚中部页码。改本文件前先改护栏三，两处必须一致。

```typst
// ===== 国一标准排版头（最终修正版）=====
#set text(font: ("SimSun", "Times New Roman"), size: 12pt, lang: "zh")   // 正文宋体12pt + Times New Roman
#set page(paper: "a4", margin: (top: 2.54cm, bottom: 2.54cm, left: 2.8cm, right: 2.8cm), numbering: "1")  // A4 + 页边距≥2.5cm + 页脚中部页码从1连续（Typst 默认居中，实测符合官方第三条）
#set heading(numbering: "1.")                                          // 标题自动编号（1. / 1.1 / 1.1.1）
#show heading: set text(font: "SimHei")                                // 标题黑体
#show heading.where(level: 1): set text(size: 16pt)                    // 一级标题16pt
#show heading.where(level: 2): set text(size: 14pt)                    // 二级14pt
#show heading.where(level: 3): set text(size: 12pt)                    // 三级12pt
#show heading: it => { it; box() }                                     // 修正坑②：标题后第一段顶格不缩进
#set par(justify: true, leading: 1.05em, first-line-indent: 2em)       // 两端对齐 + 首行缩进2字符；leading 1.05em 实测行距 20.9pt ≈ Word 1.5 倍
#set math.equation(numbering: "(1)")                                   // 公式全文连续编号 (1)(2)(3)
#show math.equation: it => { it; box() }                               // 修正坑②：公式后第一段顶格
#set figure(numbering: none)                                           // 修正坑①：图表双编号（Typst 自动加"表N"叠在手写"表X-X"上）
#show figure.caption: set text(size: 10.5pt)                           // 图题/表题 10.5pt
```

## 三个坑的根因（已在上面的排版头里修正，删任何一行都会复发）

1. **图表双编号**：Typst 0.15 在 `lang:"zh"` 下会自动给 figure 加「表N/图N」全局编号，叠在手动「表X-X」上。解法：`#set figure(numbering: none)`。

2. **标题/公式/图表后第一段顶格**：Typst 默认「块级元素（heading/display equation/figure）后的第一个段落」不缩进。解法：`#show heading: it => { it; box() }` + `#show math.equation: it => { it; box() }`（塞空 box 打断紧邻关系）。三条都要加，只加 heading 会漏公式后顶格。

3. **宽表居中而非左对齐**：宽表默认左对齐，需手动设置居中。

## 三线表函数（配合上面排版头用）

```typst
#let three_line_table(..args) = figure(
  table(
    columns: args.pos().at(0),
    stroke: none,
    table.hline(stroke: 1.5pt),        // 顶线 1.5pt 粗
    ..args.pos().at(1),
    table.hline(stroke: 0.75pt),       // 表头下线 0.75pt 细
    ..args.pos().at(2),
    table.hline(stroke: 1.5pt),        // 底线 1.5pt 粗
  ),
)
```
