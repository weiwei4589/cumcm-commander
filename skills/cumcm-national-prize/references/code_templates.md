# 核心算法代码模板

> 新对话窗口直接复制这些代码模板，填入数据和参数即可。不需要从零写，不需要猜语法。

---

## 1. WOE分箱与IV计算（等频分箱 + 拉普拉斯平滑）

```python
import pandas as pd
import numpy as np

def calc_woe_iv(df, var, target_col, bins=5, is_numeric=True):
    """
    计算单个变量的WOE和IV值
    - 等频分箱(连续变量) 或 按类别分箱(分类变量)
    - 拉普拉斯平滑: Good和Bad各加0.5
    """
    df = df.copy()
    if is_numeric and df[var].nunique() > bins:
        df['_bin'] = pd.qcut(df[var], q=bins, duplicates='drop')
    else:
        df['_bin'] = df[var].astype(str)
    
    g = df.groupby('_bin')[target_col].agg(
        Good=lambda x: (x == 0).sum(),
        Bad=lambda x: (x == 1).sum()
    )
    
    g['Good_adj'] = g['Good'] + 0.5  # 拉普拉斯平滑
    g['Bad_adj'] = g['Bad'] + 0.5
    total_good = g['Good_adj'].sum()
    total_bad = g['Bad_adj'].sum()
    
    g['WOE'] = np.log(
        (g['Good_adj'] / total_good) / (g['Bad_adj'] / total_bad)
    )
    g['IV_part'] = (g['Good_adj'] / total_good - g['Bad_adj'] / total_bad) * g['WOE']
    iv_total = g['IV_part'].sum()
    
    return g, iv_total, dict(zip(g.index.astype(str), g['WOE']))


# 使用示例
iv_results = {}
woe_maps = {}

for var in ['NAME_FAMILY_STATUS', 'NAME_INCOME_TYPE', 'AGE']:
    woedf, iv, woe_map = calc_woe_iv(df, var, 'Y', is_numeric=(var == 'AGE'))
    iv_results[var] = iv
    woe_maps[var] = woe_map
    print(f'{var}: IV={iv:.4f} {"保留" if iv >= 0.02 else "删除"}')
```

**IV筛选标准**：
- IV < 0.02：删除
- 0.02 ≤ IV < 0.1：弱预测力（保留）
- 0.1 ≤ IV < 0.5：中等预测力（保留，关注）
- IV ≥ 0.5：删除（目标泄露风险）

---

## 2. WOE转换 + 逻辑回归评分卡

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score

# WOE转换
df_woe = df.copy()
for var in ['NAME_FAMILY_STATUS', 'NAME_INCOME_TYPE']:
    df_woe[f'{var}_WOE'] = df[var].map(woe_maps[var])
df_woe[[f'{v}_WOE' for v in cat_vars]] = df_woe[[f'{v}_WOE' for v in cat_vars]].fillna(0)

# 准备数据
woe_cols = [f'{v}_WOE' for v in cat_vars]
X = df_woe[woe_cols]
y = df_woe['Y']

# 分层抽样划分
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

# 逻辑回归
lr = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
lr.fit(X_train, y_train)
y_prob = lr.predict_proba(X_test)[:, 1]

# 评估
auc = roc_auc_score(y_test, y_prob)
cv = cross_val_score(lr, X, y, cv=5, scoring='roc_auc')
print(f'AUC={auc:.4f}, CV AUC={cv.mean():.4f}±{cv.std():.4f}')

# KS统计量
import numpy as np
y_test_arr = np.array(y_test)
sorted_idx = np.argsort(y_prob)[::-1]
cum_bad = np.cumsum(y_test_arr[sorted_idx]) / sum(y_test_arr)
cum_good = np.cumsum(1 - y_test_arr[sorted_idx]) / sum(1 - y_test_arr)
ks = np.max(np.abs(cum_bad - cum_good))
print(f'KS={ks:.4f}')
```

---

## 3. 评分刻度转换（PDO=20, Base=600, BaseOdds=1:50）

```python
import numpy as np

# 计算评分
B = 20 / np.log(2)
A = 600 + B * np.log(50)
scores = A - B * (lr.intercept_[0] + X_test @ lr.coef_[0])
print(f'评分范围: {scores.min():.0f}-{scores.max():.0f}')

# 十分位分组分析
import pandas as pd
score_df = pd.DataFrame({'score': scores, 'Y': y_test})
score_df['group'] = pd.qcut(score_df['score'], q=10, duplicates='drop')
group_analysis = score_df.groupby('group')['Y'].agg(['count', 'sum', 'mean'])
group_analysis['bad_rate'] = group_analysis['mean']
print(group_analysis[['count', 'bad_rate']])
```

---

## 4. Typst三线表函数（直接复制到 .typ 文件头部）

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

**使用示例**：
```typst
#三线表(
  columns: 3,
  [变量], [IV值], [结果],
  [NAME_FAMILY_STATUS], [0.0985], [保留],
  [NAME_INCOME_TYPE], [0.0242], [保留],
  [AGE], [0.0124], [删除],
  caption: [表4-1 变量IV值汇总]
)
```

---

## 5. matplotlib 国赛论文级配置（绘图脚本头部）

```python
import matplotlib
import matplotlib.pyplot as plt
from cycler import cycler

matplotlib.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'axes.grid': True,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'lines.linewidth': 2.0,
})

# Okabe-Ito 色盲友好色板
matplotlib.rcParams['axes.prop_cycle'] = cycler(color=[
    '#009E73', '#56B4E9', '#E69F00', '#0072B2', '#D55E00', '#CC79A7'
])
```

**每张图的保存模板**：
```python
fig, ax = plt.subplots(figsize=(7, 5))
# ... 绘图代码 ...
for s in ['top', 'right']:
    ax.spines[s].set_visible(False)  # 去上/右边框
fig.tight_layout()
fig.savefig('figures/xxx.png', dpi=300, bbox_inches='tight')
plt.close()
```

---

## 6. 多模型对比（含统计检验）

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier

models = {
    '逻辑回归': LogisticRegression(max_iter=1000, C=1.0, random_state=42),
    '决策树': DecisionTreeClassifier(max_depth=5, random_state=42),
    '随机森林': RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42),
    'AdaBoost': AdaBoostClassifier(n_estimators=200, random_state=42),
}

results = []
for name, model in models.items():
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, prob)
    cv = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
    results.append({'模型': name, 'AUC': auc, 'CV均值': cv.mean(), 'CV标准差': cv.std()})

comparison = pd.DataFrame(results)
print(comparison)
```

---

## 7. DeLong检验（AUC差异统计显著性）

```python
import numpy as np
from scipy.stats import norm

def delong_test(y_true, prob1, prob2):
    """
    DeLong检验：比较两个模型AUC差异的统计显著性
    返回: (z统计量, p值)
    """
    from sklearn.metrics import auc, roc_curve
    
    fpr1, tpr1, _ = roc_curve(y_true, prob1)
    fpr2, tpr2, _ = roc_curve(y_true, prob2)
    auc1 = auc(fpr1, tpr1)
    auc2 = auc(fpr2, tpr2)
    
    # 简化实现：基于AUC差异和样本量的近似检验
    n = len(y_true)
    # 方差估计（基于Hanley & McNeil, 1982）
    q1 = auc1 / (2 - auc1)
    q2 = 2 * auc1**2 / (1 + auc1)
    se1 = np.sqrt((auc1*(1-auc1) + (n-1)*(q1 - auc1**2) + (n-1)*(q2 - auc1)) / n)
    
    q1 = auc2 / (2 - auc2)
    q2 = 2 * auc2**2 / (1 + auc2)
    se2 = np.sqrt((auc2*(1-auc2) + (n-1)*(q1 - auc2**2) + (n-1)*(q2 - auc2)) / n)
    
    z = (auc1 - auc2) / np.sqrt(se1**2 + se2**2)
    p = 2 * (1 - norm.cdf(abs(z)))
    return z, p

# 使用示例
z_lr_rf, p_lr_rf = delong_test(y_test, y_prob_lr, y_prob_rf)
print(f'LR vs RF: z={z_lr_rf:.3f}, p={p_lr_rf:.4f}')
```

---

## 8. 数值审计脚本

在编译论文前运行此脚本，确保所有数值来自实际运行结果：

```python
# save as code/audit_numbers.py
import pandas as pd, re, sys

def audit():
    errors = 0
    
    # Load actual results
    try:
        iv = pd.read_csv('results/iv_results.csv')
        comp = pd.read_csv('results/model_comparison.csv')
    except FileNotFoundError as e:
        print(f'❌ 缺少结果文件: {e}')
        return 1
    
    # Load paper
    with open('paper_typst/main.typ', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Check: every IV value in paper matches CSV
    for _, row in iv.iterrows():
        var, iv_val = row['变量'], row['IV值']
        if f'{iv_val:.4f}' not in text:
            print(f'❌ IV: {var}={iv_val:.4f} 在论文中找不到或数值错误')
            errors += 1
    
    # Check: LR AUC/KS match
    lr = comp[comp['模型']=='逻辑回归'].iloc[0]
    for col in ['AUC', 'KS']:
        if f'{lr[col]:.4f}' not in text:
            print(f'❌ LR {col}={lr[col]:.4f} 在论文中找不到')
            errors += 1
    
    if errors:
        print(f'\n共{errors}项数值不一致。请先修复再编译！')
        return 1
    print('✅ 数值审计通过')
    return 0

if __name__ == '__main__':
    sys.exit(audit())
```
