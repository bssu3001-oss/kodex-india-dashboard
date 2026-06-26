#!/usr/bin/env python3
"""로컬 서버: 대시보드 서빙 + /api/rebuild 엔드포인트로 데이터 갱신.

build.py 가 한 번 빌드하고 끝나는 반면, 이 서버는 떠 있는 동안
브라우저의 '데이터 갱신' 버튼·자동 갱신이 /api/rebuild 를 호출하면
build() 를 다시 돌려 최신 데이터로 dashboard.html 을 재생성한다.
표준 라이브러리만 사용한다.
"""
import http.server
import socketserver
import os
import sys
import json
import threading
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import build

DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_POST(self):
        if self.path.rstrip("/") == "/api/rebuild":
            try:
                build(open_browser=False)
                self._send_json({"ok": True})
            except Exception as e:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_error(404)

    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # 재빌드 후 새로고침이 항상 최신 파일을 받도록 캐시 비활성화
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass  # 콘솔 조용히


def main():
    os.chdir(DIR)
    url = "http://localhost:%d/dashboard.html" % PORT

    # dashboard.html 이 없으면(첫 실행) 한 번은 동기로 빌드
    if not os.path.exists(os.path.join(DIR, "dashboard.html")):
        print("📊  초기 빌드 중...")
        try:
            build(open_browser=False)
        except Exception as e:  # noqa: BLE001
            print("⚠️   초기 빌드 실패:", e)

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", PORT), Handler)
    print("🌐  서버 실행 중:", url)
    print("    종료하려면 이 창에서 Ctrl+C")

    # 서버는 즉시 응답하고, 최신 데이터 갱신은 백그라운드로 (야후 호출이 느려도 안 막힘)
    def _initial_refresh():
        try:
            print("📊  최신 데이터로 갱신 중...")
            build(open_browser=False)
            print("✅  초기 갱신 완료 — 브라우저에서 '데이터 갱신'을 누르거나 새로고침하면 반영됩니다.")
        except Exception as e:  # noqa: BLE001
            print("⚠️   초기 갱신 실패(기존 데이터로 표시):", e)

    threading.Thread(target=_initial_refresh, daemon=True).start()

    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
