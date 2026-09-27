"""数值审计脚本——验证论文中的数值与CSV结果一致。"""
import pandas as pd, os, sys

def audit(csv_dir='results', paper_dir='paper'):
    errors = []
    try: iv = pd.read_csv(os.path.join(csv_dir, 'iv_results.csv'))
    except: iv = None
    try: comp = pd.read_csv(os.path.join(csv_dir, 'model_comparison.csv'))
    except: comp = None
    
    paper_files = []
    for ext in ['.typ', '.tex', '.md']:
        paper_files.extend([os.path.join(paper_dir, f) for f in os.listdir(paper_dir) if f.endswith(ext)])
    if not paper_files:
        print('No paper source files found'); return
    
    text = ''
    for pf in paper_files:
        with open(pf, 'r', encoding='utf-8') as f: text += f.read()
    
    if iv is not None:
        for _, row in iv.iterrows():
            v = str(row.iloc[0]); ivs = f'{float(row.iloc[1]):.4f}'
            if ivs not in text: errors.append(f'IV {v}={ivs} missing')
    
    if comp is not None:
        for _, row in comp.iterrows():
            for col in ['AUC','KS']:
                if col in comp.columns:
                    val = f'{row[col]:.4f}'
                    if val not in text: errors.append(f'{col}={val} missing')
    
    if errors:
        print(f'FAILED: {len(errors)} mismatches')
        for e in errors: print(f'  {e}')
        sys.exit(1)
    else: print('PASSED')

if __name__ == '__main__': audit()
