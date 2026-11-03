#!/usr/bin/env python3
"""Copy web/almanchara.html -> app/src/main/assets/index.html with the small
changes the Android WebView needs. Run it again whenever you update the web app.

    python3 tools/apply_android_patches.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "almanchara.html"
DST = ROOT / "app" / "src" / "main" / "assets" / "index.html"

# window.print() -> native Android print dialog (also allows "Save as PDF")
PRINT_SHIM = r"""
<script id="android-shim">(function(){if(!window.AndroidBridge)return;window.print=function(){try{AndroidBridge.print();}catch(e){}};})();</script>"""

# Blob + <a download> does not work in WebView -> hand the file to the native save dialog
DOWNLOAD_HOOK = (
    "if(window.AndroidBridge&&AndroidBridge.saveFile){try{"
    "const u8=new TextEncoder().encode('\\ufeff'+content);let s='';"
    "for(let i=0;i<u8.length;i+=8192)s+=String.fromCharCode.apply(null,u8.subarray(i,i+8192));"
    "AndroidBridge.saveFile(String(name),btoa(s),String(type||'application/octet-stream').split(';')[0]);"
    "return;}catch(e){}}"
)

# (old, new) pairs - each `old` must appear exactly once
PATCHES = [
    ('<meta charset="UTF-8">', '<meta charset="UTF-8">' + PRINT_SHIM),
    ('<link rel="manifest" href="manifest.webmanifest">', ''),
    ('function download(name,content,type){', 'function download(name,content,type){' + DOWNLOAD_HOOK),
    ('if("serviceWorker" in navigator && location.protocol!=="file:")',
     'if(!window.AndroidBridge&&"serviceWorker" in navigator && location.protocol!=="file:")'),
]


def main():
    html = SRC.read_text(encoding="utf-8")
    for old, new in PATCHES:
        n = html.count(old)
        if n != 1:
            sys.exit(f"patch target found {n} times (expected 1): {old[:60]!r}\n"
                     "The web app changed - update PATCHES in this script.")
        html = html.replace(old, new)
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(html, encoding="utf-8")
    print(f"wrote {DST.relative_to(ROOT)} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
