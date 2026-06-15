import pandas as pd
import numpy as np

np.random.seed(42)

groups = ['A组', 'B组', 'C组']
data = []

for group in groups:
    if group == 'A组':
        n = 10
        values = np.random.normal(loc=50, scale=10, size=n)
    elif group == 'B组':
        n = 8
        values = np.random.normal(loc=65, scale=15, size=n)
    else:
        n = 5
        values = np.random.normal(loc=45, scale=8, size=n)
    for v in values:
        data.append({'组别': group, '数值': round(v, 2)})

df = pd.DataFrame(data)
df.to_csv('small_sample_data.csv', index=False, encoding='utf-8-sig')
print(f'小样本数据已生成：{len(df)} 行')
print(df)
print('\n各组数据量：')
print(df.groupby('组别')['数值'].count())
