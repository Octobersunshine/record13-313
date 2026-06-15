import urllib.request
import urllib.error
import json
import base64

PORT = 5001
BASE_URL = f'http://127.0.0.1:{PORT}'

print('=== 测试自动带宽调整修复 ===\n')

def upload_test(filename, desc):
    print(f'【{desc}】')
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
    uploaded_name = result.get('filename')
    print(f'  上传成功: {uploaded_name}, 行数: {result.get("total_rows")}')
    return uploaded_name

def test_violin(filename, x_col, y_col, desc):
    print(f'\n【{desc}】')
    url = f'{BASE_URL}/api/violin'
    data = json.dumps({
        'filename': filename,
        'x_col': x_col,
        'y_col': y_col,
        'title': desc
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode('utf-8'))
    
    if result.get('success'):
        bw = result.get('bw_adjust')
        print(f'  自动带宽调整因子: {bw}')
        img_b64 = result['image']
        img_bytes = base64.b64decode(img_b64)
        print(f'  图片大小: {len(img_bytes)} 字节')
        print(f'  PNG 格式正确: {img_bytes[:8].hex() == "89504e470d0a1a0a"}')
        
        stats = result.get('statistics', {})
        print(f'  统计组数: {len(stats)}')
        for group, s in stats.items():
            print(f'    - {group}: n={s["count"]}, 均值={s["mean"]:.2f}')
        
        suffix = 'small' if '小' in desc else 'large'
        with open(f'fixed_violin_{suffix}.png', 'wb') as f:
            f.write(img_bytes)
        print(f'  图片已保存: fixed_violin_{suffix}.png')
    else:
        print(f'  错误: {result.get("error")}')
    
    return result

print('=' * 50)
print('测试 1: 小样本数据 (23行, 分组测试)')
print('=' * 50)
small_file = upload_test('small_sample_data.csv', '上传小样本数据')
test_violin(small_file, '组别', '数值', '小样本分组小提琴图')

print()
print('=' * 50)
print('测试 2: 小样本数据 (23行, 单变量测试)')
print('=' * 50)
test_violin(small_file, None, '数值', '小样本单变量小提琴图')

print()
print('=' * 50)
print('测试 3: 大样本数据 (800行, 分组测试)')
print('=' * 50)
large_file = upload_test('sample_data.csv', '上传大样本数据')
test_violin(large_file, '组别', '数值', '大样本分组小提琴图')

print()
print('=' * 50)
print('测试 4: 大样本数据 (800行, 单变量测试)')
print('=' * 50)
test_violin(large_file, None, '数值', '大样本单变量小提琴图')

print()
print('=' * 50)
print('带宽调整规则验证:')
print('=' * 50)
from app import calculate_bw_adjust
import pandas as pd

test_cases = [
    (300, 'n >= 100'),
    (75, '50 <= n < 100'),
    (40, '30 <= n < 50'),
    (25, '20 <= n < 30'),
    (15, '10 <= n < 20'),
    (7, '5 <= n < 10'),
    (3, 'n < 5'),
]

df_test = pd.DataFrame({'x': ['A'] * 1000, 'y': range(1000)})
for n, desc in test_cases:
    df_slice = pd.DataFrame({'x': ['A'] * n, 'y': range(n)})
    bw = calculate_bw_adjust(df_slice, 'x', 'y')
    print(f'  {desc:20} (n={n:3d}): bw_adjust = {bw}')

print()
print('=== 测试完成 ===')
