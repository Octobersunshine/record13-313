import requests
import json

print('=== 测试小提琴图服务 ===\n')

url = 'http://127.0.0.1:5000/api/upload'
files = {'file': open('sample_data.csv', 'rb')}
response = requests.post(url, files=files)
result = response.json()

print('【1. 文件上传测试】')
print(f'  成功: {result.get("success")}')
print(f'  文件名: {result.get("filename")}')
print(f'  行数: {result.get("total_rows")}')
print(f'  列: {result.get("columns")}')
print(f'  数值列: {result.get("numeric_columns")}')
print()

if result.get('success'):
    url2 = 'http://127.0.0.1:5000/api/violin'
    data = {
        'filename': result['filename'],
        'x_col': '组别',
        'y_col': '数值',
        'title': '测试小提琴图'
    }
    response2 = requests.post(url2, json=data)
    result2 = response2.json()

    print('【2. 生成小提琴图测试】')
    print(f'  成功: {result2.get("success")}')
    if result2.get('success'):
        img_len = len(result2['image'])
        print(f'  图片(base64)长度: {img_len} 字符')
        print(f'  统计组数: {len(result2.get("statistics", {}))}')
        for group, stats in result2.get('statistics', {}).items():
            print(f'    - {group}:')
            print(f'        计数: {stats["count"]}')
            print(f'        均值: {stats["mean"]:.2f}')
            print(f'        中位数: {stats["median"]:.2f}')
            print(f'        标准差: {stats["std"]:.2f}')
            print(f'        最小/最大: {stats["min"]:.2f} / {stats["max"]:.2f}')
    else:
        print(f'  错误: {result2.get("error")}')

    print()
    print('【3. 单变量小提琴图测试（不分分组）】')
    data3 = {
        'filename': result['filename'],
        'x_col': None,
        'y_col': '数值',
        'title': '单变量小提琴图'
    }
    response3 = requests.post(url2, json=data3)
    result3 = response3.json()
    print(f'  成功: {result3.get("success")}')
    if result3.get('success'):
        print(f'  图片(base64)长度: {len(result3["image"])} 字符')
        print(f'  统计信息: {list(result3.get("statistics", {}).keys())}')
    else:
        print(f'  错误: {result3.get("error")}')

print()
print('=== 测试完成 ===')
