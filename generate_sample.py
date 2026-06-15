import pandas as pd
import numpy as np

np.random.seed(42)

n = 200

groups = ['A组', 'B组', 'C组', 'D组']
data = []
for group in groups:
    if group == 'A组':
        values = np.random.normal(loc=50, scale=10, size=n)
    elif group == 'B组':
        values = np.random.normal(loc=65, scale=15, size=n)
    elif group == 'C组':
        values = np.random.normal(loc=45, scale=8, size=n)
    else:
        values = np.random.normal(loc=70, scale=12, size=n)
    for v in values:
        data.append({'组别': group, '数值': round(v, 2)})

df = pd.DataFrame(data)
df.to_csv('sample_data.csv', index=False, encoding='utf-8-sig')
print(f'示例数据已生成：{len(df)} 行')
print(df.head())
print('\n各组统计：')
print(df.groupby('组别')['数值'].describe())
