import urllib.request
import urllib.error
import json
import base64

PORT = 5001
BASE_URL = f'http://127.0.0.1:{PORT}'

print('=' * 60)
print('测试增强版分组小提琴图功能')
print('=' * 60)
print()

def upload_file(filename):
    url = f'{BASE_URL}/api/upload'
    with open(filename, 'rb') as f:
        file_data = f.read()
    
    boundary = '----TestBoundary123456'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: text/csv\r\n\r\n'
    ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode('utf-8'))
    return result

def test_violin(desc, **kwargs):
    print(f'【{desc}】')
    url = f'{BASE_URL}/api/violin'
    data = json.dumps(kwargs).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get('success'):
            print(f'  ✓ 成功')
            print(f'  带宽调整: {result.get("bw_adjust")}x')
            print(f'  统计组数: {len(result.get("statistics", {}))}')
            img_bytes = base64.b64decode(result['image'])
            print(f'  图片大小: {len(img_bytes)} 字节')
            print(f'  PNG有效: {img_bytes[:8].hex() == "89504e470d0a1a0a"}')
            
            safe_name = desc.replace(' ', '_').replace('(', '').replace(')', '')
            with open(f'test_{safe_name}.png', 'wb') as f:
                f.write(img_bytes)
            print(f'  已保存: test_{safe_name}.png')
        else:
            print(f'  ✗ 失败: {result.get("error")}')
    except urllib.error.HTTPError as e:
        print(f'  ✗ HTTP错误: {e.code}')
        print('  响应:', e.read().decode('utf-8')[:300])
    except Exception as e:
        print(f'  ✗ 异常: {type(e).__name__}: {e}')
    print()

print('【上传测试数据】')
result = upload_file('grouped_sample_data.csv')
print(f'  成功: {result.get("success")}')
print(f'  行数: {result.get("total_rows")}')
print(f'  数值列: {result.get("numeric_columns")}')
print(f'  分类列: {result.get("categorical_columns")}')
print(f'  配色方案: {len(result.get("palettes", []))} 种')
print(f'  内部显示选项: {len(result.get("inner_options", []))} 种')
print()
filename = result.get('filename')

test_cases = [
    ('基础分组 - 按班级分组', {
        'filename': filename,
        'x_col': '班级',
        'y_col': '考试成绩',
        'title': '各班级考试成绩分布'
    }),
    ('嵌套分组 - 班级+性别', {
        'filename': filename,
        'x_col': '班级',
        'y_col': '考试成绩',
        'hue_col': '性别',
        'title': '各班级男女考试成绩分布'
    }),
    ('水平方向 - 完成时间', {
        'filename': filename,
        'x_col': '班级',
        'y_col': '完成时间(分钟)',
        'orient': 'h',
        'title': '各班级完成时间分布 (水平)'
    }),
    ('四分位数内部显示', {
        'filename': filename,
        'x_col': '班级',
        'y_col': '考试成绩',
        'inner': 'quartile',
        'title': '各班级成绩分布 (四分位数显示)'
    }),
    ('使用 Set1 鲜艳配色', {
        'filename': filename,
        'x_col': '班级',
        'y_col': '考试成绩',
        'palette': 'Set1',
        'title': '各班级成绩分布 (Set1配色)'
    }),
    ('使用 viridis 配色', {
        'filename': filename,
        'x_col': '班级',
        'y_col': '考试成绩',
        'palette': 'viridis',
        'title': '各班级成绩分布 (Viridis配色)'
    }),
    ('多指标对比 - 成绩+时间', {
        'filename': filename,
        'x_col': '班级',
        'y_cols': ['考试成绩', '完成时间(分钟)'],
        'title': '各班级成绩与完成时间对比'
    }),
    ('多指标+嵌套分组', {
        'filename': filename,
        'x_col': '班级',
        'y_cols': ['考试成绩', '完成时间(分钟)'],
        'hue_col': '性别',
        'title': '各班级男女成绩与时间对比'
    }),
    ('不分组 - 单变量分布', {
        'filename': filename,
        'y_col': '考试成绩',
        'title': '整体考试成绩分布'
    }),
]

for desc, params in test_cases:
    test_violin(desc, **params)

print('=' * 60)
print('所有测试完成！')
print('=' * 60)
