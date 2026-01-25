#!/bin/bash
# Xcode 설치 후 Swift 도구 활성화 스크립트

echo "🍎 Swift 도구 설정 시작..."

# 1. Xcode 경로 설정
if [ -d "/Applications/Xcode.app" ]; then
    echo "→ Xcode 경로 설정..."
    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
    
    echo "→ 라이선스 동의..."
    sudo xcodebuild -license accept 2>/dev/null || true
    
    # 2. swiftlint 테스트
    echo "→ swiftlint 테스트..."
    if [ -f "$HOME/bin/swiftlint" ]; then
        $HOME/bin/swiftlint version && echo "✅ swiftlint 작동"
    fi
    
    # 3. sitrep 설치
    echo "→ sitrep 설치..."
    mint install twostraws/Sitrep 2>/dev/null || echo "sitrep 설치 실패 (수동 설치 필요)"
    
    echo "✅ Swift 도구 설정 완료!"
else
    echo "❌ Xcode가 /Applications/Xcode.app에 없습니다."
fi
