import urllib.request
import urllib.error
import json

print('=== 测试小提琴图服务 ===\n')

try:
    resp = urllib.request.urlopen('http://127.0.0.1:5000/')
    html = resp.read().decode('utf-8')
    print('首页状态码:', resp.status)
    print('首页内容长度:', len(html))
    print('首页包含"小提琴图":', '小提琴图' in html)
except urllib.error.URLError as e:
    print('首页访问失败:', e)

print()

try:
    url = 'http://127.0.0.1:5000/api/upload'
    with open('sample_data.csv', 'rb') as f:
        file_data = f.read()
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="sample_data.csv"\r\n'
        f'Content-Type: text/csv\r\n\r\n'
    ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode('utf-8'))
    print('上传测试:')
    print('  成功:', result.get('success'))
    print('  文件名:', result.get('filename'))
    print('  行数:', result.get('total_rows'))
    print('  列:', result.get('columns'))
except urllib.error.HTTPError as e:
    print('上传HTTP错误:', e.code, e.reason)
    print('响应:', e.read().decode('utf-8')[:500])
except Exception as e:
    print('上传失败:', type(e).__name__, str(e))
