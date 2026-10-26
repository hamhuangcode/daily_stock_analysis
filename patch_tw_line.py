from pathlib import Path
from opencc import OpenCC

cc = OpenCC('s2twp')

# 1. 將專案裡所有模板與 AI 提示詞轉為台灣繁體中文
for folder in ['src', 'templates', 'bot', 'data_provider']:
    p = Path(folder)
    if p.exists():
        for file_path in p.rglob('*'):
            if file_path.suffix in ('.py', '.j2', '.md', '.txt', '.json', '.html'):
                try:
                    text = file_path.read_text(encoding='utf-8')
                    text = text.replace('请使用中文', '請務必使用台灣繁體中文(Traditional Chinese)')
                    text = text.replace('用中文', '用台灣繁體中文')
                    text = cc.convert(text)
                    file_path.write_text(text, encoding='utf-8')
                except Exception as e:
                    print(f"跳過檔案 {file_path}: {e}")

print("✅ 第一步：已將所有系統模板與 AI 提示詞轉為台灣繁體中文！")

# 2. 建立 sitecustomize.py（Python 啟動時會自動執行，完全不需修改 main.py！）
sitecustomize_code = """# === 自動載入：強制台灣繁體中文 Email 攔截器 ===
try:
    from opencc import OpenCC
    _cc = OpenCC('s2twp')

    # 攔截 1：在 MIMEText 把文字壓成 Base64 之前，先把所有 Email 內文轉為繁體中文
    import email.mime.text
    _orig_mimetext_init = email.mime.text.MIMEText.__init__
    def _tw_mimetext_init(self, _text, _subtype='plain', _charset=None, *, policy=None):
        if isinstance(_text, str):
            _text = _cc.convert(_text)
        _orig_mimetext_init(self, _text, _subtype, _charset, policy=policy)
    email.mime.text.MIMEText.__init__ = _tw_mimetext_init

    # 攔截 2：在 Header 編碼 Email 標題與寄件人名稱之前，先轉為繁體中文
    import email.header
    _orig_header_init = email.header.Header.__init__
    def _tw_header_init(self, s=None, charset=None, maxlinelen=None, header_name=None, continuation_ws=' ', errors='strict'):
        if isinstance(s, str):
            s = _cc.convert(s)
        _orig_header_init(self, s, charset, maxlinelen, header_name, continuation_ws, errors)
    email.header.Header.__init__ = _tw_header_init

    # 攔截 3：若直接設定 msg['Subject'] = '...'，也自動轉為繁體中文
    import email.message
    _orig_setitem = email.message.Message.__setitem__
    def _tw_setitem(self, name, val):
        if isinstance(val, str):
            val = _cc.convert(val)
        _orig_setitem(self, name, val)
    email.message.Message.__setitem__ = _tw_setitem

    print("✅ 執行期 Email (MIMEText / Subject) 繁體中文攔截器已自動啟動！")
except Exception as _e:
    print(f"⚠️ 繁體攔截器啟動失敗: {_e}")
"""

# 寫入到當前目錄的 sitecustomize.py，並確保 PYTHONPATH 包含當前目錄
Path('sitecustomize.py').write_text(sitecustomize_code, encoding='utf-8')

# 若 main.py 需要插入，則安全地插在 from __future__ 之後作為雙重保障
main_file = Path('main.py')
if main_file.exists():
    original_code = main_file.read_text(encoding='utf-8')
    lines = original_code.splitlines(True)
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('from __future__'):
            insert_idx = i + 1
    lines.insert(insert_idx, "import sitecustomize\n")
    main_file.write_text("".join(lines), encoding='utf-8')

print("✅ 第二步：已安全掛載繁體中文 Email 攔截器（保留 __future__ 在第一行）！")
