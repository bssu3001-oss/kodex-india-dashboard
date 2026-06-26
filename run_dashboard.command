#!/bin/bash
# KODEX 인도Nifty50 대시보드 실행기
# 이 파일을 macOS에서 더블클릭하면 대시보드가 자동으로 생성되고 브라우저에서 열립니다.

# Change to the directory where this script lives
cd "$(dirname "$0")"

# Run the build script
python3 build.py

# If build failed, show error and pause so user can read it
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 오류가 발생했습니다. 위의 메시지를 확인해주세요."
    echo "아무 키나 누르면 창이 닫힙니다..."
    read -n 1
fi
