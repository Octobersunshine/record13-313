import urllib.request
import urllib.error
import json
import base64

PORT = 5001
BASE_URL = f'http://127.0.0.1:{PORT}'

print('=== 测试小提琴图服务 ===\n')

try:
    resp = urllib.request.urlopen(f'{BASE_URL}/')
    html = resp.read().decode('utf-8')
    print('【1. 首页测试】')
    print('  状态码:', resp.status)
    print('  内容长度:', len(html))
    print('  包含"小提琴图":', '小提琴图' in html)
except urllib.error.URLError as e:
    print('首页访问失败:', e)

print()

try:
    url = f'{BASE_URL}/api/upload'
    with open('sample_data.csv', 'rb') as f:
        file_data = f.read()
    
    boundary = '----TestBoundary123456'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="sample_data.csv"\r\n'
        f'Content-Type: text/csv\r\n\r\n'
    ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode('utf-8'))
    print('【2. 文件上传测试】')
    print('  成功:', result.get('success'))
    print('  文件名:', result.get('filename'))
    print('  行数:', result.get('total_rows'))
    print('  列:', result.get('columns'))
    print('  数值列:', result.get('numeric_columns'))
    
    filename = result.get('filename')
except urllib.error.HTTPError as e:
    print('上传HTTP错误:', e.code, e.reason)
    print('响应:', e.read().decode('utf-8')[:500])
    exit(1)
except Exception as e:
    print('上传失败:', type(e).__name__, str(e))
    exit(1)

print()

if filename:
    try:
        url2 = f'{BASE_URL}/api/violin'
        data = json.dumps({
            'filename': filename,
            'x_col': '组别',
            'y_col': '数值',
            'title': '测试小提琴图'
        }).encode('utf-8')
        
        req2 = urllib.request.Request(url2, data=data, method='POST')
        req2.add_header('Content-Type', 'application/json')
        
        resp2 = urllib.request.urlopen(req2)
        result2 = json.loads(resp2.read().decode('utf-8'))
        
        print('【3. 分组小提琴图测试】')
        print('  成功:', result2.get('success'))
        if result2.get('success'):
            img_b64 = result2['image']
            print('  图片(base64)长度:', len(img_b64), '字符')
            img_bytes = base64.b64decode(img_b64)
            print('  图片大小:', len(img_bytes), '字节')
            print('  PNG头部验证:', img_bytes[:8].hex() == '89504e470d0a1a0a')
            
            stats = result2.get('statistics', {})
            print('  统计组数:', len(stats))
            for group, s in stats.items():
                print(f'    - {group}: 均值={s["mean"]:.2f}, 中位数={s["median"]:.2f}, n={s["count"]}')
            
            with open('test_violin_output.png', 'wb') as f:
                f.write(img_bytes)
            print('  图片已保存为 test_violin_output.png')
        else:
            print('  错误:', result2.get('error'))
    except urllib.error.HTTPError as e:
        print('生成图表HTTP错误:', e.code, e.reason)
        print('响应:', e.read().decode('utf-8')[:500])
    except Exception as e:
        print('生成图表失败:', type(e).__name__, str(e))

print()

if filename:
    try:
        url3 = f'{BASE_URL}/api/violin'
        data3 = json.dumps({
            'filename': filename,
            'x_col': None,
            'y_col': '数值',
            'title': '单变量小提琴图'
        }).encode('utf-8')
        
        req3 = urllib.request.Request(url3, data=data3, method='POST')
        req3.add_header('Content-Type', 'application/json')
        
        resp3 = urllib.request.urlopen(req3)
        result3 = json.loads(resp3.read().decode('utf-8'))
        
        print('【4. 单变量小提琴图测试】')
        print('  成功:', result3.get('success'))
        if result3.get('success'):
            print('  图片(base64)长度:', len(result3['image']), '字符')
            stats3 = result3.get('statistics', {})
            print('  统计键:', list(stats3.keys()))
        else:
            print('  错误:', result3.get('error'))
    except Exception as e:
        print('单变量测试失败:', type(e).__name__, str(e))

print()
print('=== 测试完成 ===')
