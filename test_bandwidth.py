import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

df = pd.read_csv('small_sample_data.csv')

print('=== 测试小数据量下的小提琴图 ===')
print(f'总数据量: {len(df)}')
print(f'各组数据量: {dict(df.groupby("组别")["数值"].count())}')
print()

def test_violin(bw_adjust=None, filename_suffix=''):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.set_style("whitegrid")
    
    if bw_adjust is not None:
        sns.violinplot(data=df, x='组别', y='数值', ax=axes[0], inner='box', bw_adjust=bw_adjust)
        sns.violinplot(data=df, y='数值', ax=axes[1], inner='box', bw_adjust=bw_adjust)
    else:
        sns.violinplot(data=df, x='组别', y='数值', ax=axes[0], inner='box')
        sns.violinplot(data=df, y='数值', ax=axes[1], inner='box')
    
    axes[0].set_title(f'分组小提琴图 (bw_adjust={bw_adjust})')
    axes[1].set_title(f'单变量小提琴图 (bw_adjust={bw_adjust})')
    plt.tight_layout()
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    
    with open(f'test_small_sample_{filename_suffix}.png', 'bw') as f:
        f.write(buf.getvalue())
    print(f'已保存: test_small_sample_{filename_suffix}.png')

print('【1. 默认带宽】')
test_violin(bw_adjust=None, filename_suffix='default')

print()
print('【2. 带宽 x1.2】')
test_violin(bw_adjust=1.2, filename_suffix='bw1.2')

print()
print('【3. 带宽 x1.5】')
test_violin(bw_adjust=1.5, filename_suffix='bw1.5')

print()
print('【4. 带宽 x2.0】')
test_violin(bw_adjust=2.0, filename_suffix='bw2.0')

print()
print('=== 测试完成 ===')
