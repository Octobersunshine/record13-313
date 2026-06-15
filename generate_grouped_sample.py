import pandas as pd
import numpy as np

np.random.seed(42)

n_per_group = 100
groups = ['A组', 'B组', 'C组']
genders = ['男', '女']
data = []

for group in groups:
    for gender in genders:
        if group == 'A组':
            score_mu = 75 if gender == '男' else 80
            score_sigma = 10
            time_mu = 45 if gender == '男' else 50
            time_sigma = 8
        elif group == 'B组':
            score_mu = 65 if gender == '男' else 70
            score_sigma = 12
            time_mu = 55 if gender == '男' else 60
            time_sigma = 10
        else:
            score_mu = 85 if gender == '男' else 88
            score_sigma = 8
            time_mu = 40 if gender == '男' else 42
            time_sigma = 6

        scores = np.random.normal(loc=score_mu, scale=score_sigma, size=n_per_group)
        times = np.random.normal(loc=time_mu, scale=time_sigma, size=n_per_group)

        for i in range(n_per_group):
            data.append({
                '班级': group,
                '性别': gender,
                '考试成绩': round(scores[i], 1),
                '完成时间(分钟)': round(times[i], 1)
            })

df = pd.DataFrame(data)
df.to_csv('grouped_sample_data.csv', index=False, encoding='utf-8-sig')
print(f'分组示例数据已生成：{len(df)} 行')
print(df.head())
print()
print('列名：', df.columns.tolist())
print()
print('按班级+性别分组统计：')
print(df.groupby(['班级', '性别']).agg({'考试成绩': ['count', 'mean', 'std']}))
