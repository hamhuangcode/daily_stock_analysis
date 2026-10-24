import re
from pathlib import Path

# 1. 將 templates 與 src 內所有固定簡體模板與提示詞轉為台灣繁體中文
try:
    from opencc import OpenCC
    cc = OpenCC('s2twp')
    for folder in ['src', 'templates']:
        p = Path(folder)
        if p.exists():
            for file_path in p.rglob('*'):
                if file_path.suffix in ('.py', '.j2', '.md', '.txt', '.json'):
                    try:
                        text = file_path.read_text(encoding='utf-8')
                        file_path.write_text(cc.convert(text), encoding='utf-8')
                    except Exception:
                        pass
    print("✅ 已將所有系統模板與 AI 提示詞轉為台灣繁體中文！")
except Exception as e:
    print(f"⚠️ 繁體轉換跳過: {e}")

# 2. 在 main.py 注入執行期攔截器：確保所有寄出的 Email 與 LINE 訊息強制轉繁體，且 LINE 自動分段發送（突破 5000 字限制）
main_file = Path('main.py')
if main_file.exists():
    original_code = main_file.read_text(encoding='utf-8')
    hook_code = """import os, json, urllib.request
try:
    from opencc import OpenCC
    _cc = OpenCC('s2twp')
except Exception:
    _cc = None

# 自動攔截並將所有外發 Email 轉為繁體中文
import smtplib
_orig_sendmail = smtplib.SMTP.sendmail
def _tw_sendmail(self, from_addr, to_addrs, msg, *args, **kwargs):
    if _cc:
        if isinstance(msg, bytes):
            try:
                msg = _cc.convert(msg.decode('utf-8')).encode('utf-8')
            except Exception:
                pass
        elif isinstance(msg, str):
            msg = _cc.convert(msg)
    return _orig_sendmail(self, from_addr, to_addrs, msg, *args, **kwargs)
smtplib.SMTP.sendmail = _tw_sendmail

# 自動攔截發往 LINE 的請求：轉為繁體中文並自動以 4000 字分段推播
import requests
_orig_post = requests.Session.post
def _tw_line_post(self, url, *args, **kwargs):
    if 'api.line.me/v2/bot/message/push' in str(url):
        data = kwargs.get('data')
        json_payload = kwargs.get('json')
        payload = None
        if json_payload is not None:
            payload = json_payload
        elif data is not None:
            try:
                payload = json.loads(data.decode('utf-8') if isinstance(data, bytes) else data)
            except Exception:
                pass
        if isinstance(payload, dict) and 'messages' in payload:
            new_msgs = []
            for m in payload['messages']:
                if m.get('type') == 'text' and m.get('text'):
                    txt = _cc.convert(m['text']) if _cc else m['text']
                    # 按段落切分，確保每則不超過 4000 字元
                    chunks = []
                    current = ""
                    for line in txt.splitlines(True):
                        if len(current) + len(line) > 4000:
                            chunks.append(current)
                            current = line
                        else:
                            current += line
                    if current:
                        chunks.append(current)
                    for c in chunks:
                        new_msgs.append({'type': 'text', 'text': c.strip()})
                else:
                    new_msgs.append(m)
            # LINE 單次 API 最多帶 5 個氣泡，若超過 5 個氣泡則分批呼叫
            resp = None
            for i in range(0, max(1, len(new_msgs)), 5):
                batch_payload = {'to': payload.get('to'), 'messages': new_msgs[i:i+5]}
                if 'json' in kwargs:
                    kwargs['json'] = batch_payload
                else:
                    kwargs['data'] = json.dumps(batch_payload, ensure_ascii=False).encode('utf-8')
                resp = _orig_post(self, url, *args, **kwargs)
                print(f"[LINE Push] Batch {i//5 + 1} status: {resp.status_code}, response: {resp.text}")
            return resp
    return _orig_post(self, url, *args, **kwargs)
requests.Session.post = _tw_line_post
"""
    main_file.write_text(hook_code + "\n" + original_code, encoding='utf-8')
    print("✅ 已啟用 Email 繁體化與 LINE 自動分段推播功能！")
