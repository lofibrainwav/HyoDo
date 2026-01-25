# 🔍 Cursor Review 오류 해결 가이드

**문서일**: 2025-12-17  
**오류**: `Failed to run review: insufficient funds`  
**목적**: Cursor IDE의 코드 리뷰 기능 오류 해결

---

## 🔴 오류 원인

### 가능한 원인

1. **Cursor 계정 크레딧 부족**
   - Cursor IDE의 코드 리뷰 기능은 API 크레딧을 사용
   - 계정에 충분한 크레딧이 없을 때 발생

2. **Cursor Access Token 문제**
   - `CURSOR_ACCESS_TOKEN` 환경 변수가 없거나 잘못됨
   - 토큰이 만료되었거나 유효하지 않음

3. **API 키 설정 문제**
   - Cursor IDE 설정에서 API 키가 제대로 설정되지 않음
   - 결제 정보가 연결되지 않음

---

## ✅ 해결 방법

### 1. Cursor IDE 설정 확인

1. **Cursor IDE 열기**
2. **Settings (설정) 열기**
   - `Cmd + ,` (Mac) 또는 `Ctrl + ,` (Windows/Linux)
3. **API Keys 확인**
   - Cursor → Settings → API Keys
   - OpenAI, Anthropic, 또는 다른 API 키가 설정되어 있는지 확인
4. **Billing 확인**
   - Cursor → Settings → Billing
   - 계정 크레딧 상태 확인

### 2. 환경 변수 확인

```bash
# Cursor Access Token 확인
echo $CURSOR_ACCESS_TOKEN

# .env 파일 확인
cat .env | grep CURSOR
```

### 3. 코드베이스 설정 확인

AFO 코드베이스에서 `CURSOR_ACCESS_TOKEN`은 다음 위치에서 관리됩니다:

- **config/settings.py**: `CURSOR_ACCESS_TOKEN` 필드
- **환경 변수**: `.env` 파일 또는 시스템 환경 변수

---

## 🔧 설정 방법

### CURSOR_ACCESS_TOKEN 설정

#### 방법 1: .env 파일 사용

```bash
# .env 파일에 추가
CURSOR_ACCESS_TOKEN=your_cursor_access_token_here
```

#### 방법 2: 환경 변수로 설정

```bash
export CURSOR_ACCESS_TOKEN=your_cursor_access_token_here
```

#### 방법 3: API Wallet 사용

```bash
# API Wallet에 Cursor Access Token 저장
python3 -c "
from AFO.api_wallet import APIWallet
wallet = APIWallet()
wallet.add('cursor_access_token', 'your_token_here', service='cursor')
"
```

---

## 📋 확인 사항

### 1. Cursor IDE 계정 상태

- [ ] Cursor IDE에 로그인되어 있는가?
- [ ] 계정에 충분한 크레딧이 있는가?
- [ ] 결제 정보가 연결되어 있는가?

### 2. API 키 설정

- [ ] Cursor IDE Settings에서 API 키가 설정되어 있는가?
- [ ] API 키가 유효한가?
- [ ] API 키에 충분한 크레딧이 있는가?

### 3. 환경 변수

- [ ] `CURSOR_ACCESS_TOKEN` 환경 변수가 설정되어 있는가?
- [ ] `.env` 파일에 `CURSOR_ACCESS_TOKEN`이 있는가?
- [ ] `config/settings.py`에서 `CURSOR_ACCESS_TOKEN`이 로드되는가?

---

## 🎯 권장 사항

### 1. Cursor IDE 설정 우선

- Cursor IDE의 내장 설정을 우선 사용
- 환경 변수는 보조적으로 사용

### 2. 크레딧 모니터링

- Cursor IDE에서 크레딧 사용량 모니터링
- 크레딧이 부족하면 충전

### 3. Review 기능 사용 제한

- 필요할 때만 Review 기능 사용
- 대규모 파일 리뷰는 비용이 많이 들 수 있음

---

## ⚠️ 주의사항

1. **Review 기능은 유료 서비스**
   - Cursor IDE의 코드 리뷰 기능은 API 크레딧을 사용
   - 크레딧이 부족하면 오류 발생

2. **환경 변수 vs IDE 설정**
   - Cursor IDE의 내장 설정이 우선
   - 환경 변수는 추가 설정용

3. **토큰 보안**
   - `CURSOR_ACCESS_TOKEN`은 민감 정보
   - `.env` 파일을 `.gitignore`에 추가
   - Git에 커밋하지 않도록 주의

---

## 📝 관련 파일

- `config/settings.py`: `CURSOR_ACCESS_TOKEN` 필드 정의
- `.env`: 환경 변수 설정 (로컬)
- `docs/afo/CURSOR_REVIEW_ERROR_GUIDE.md`: 이 문서

---

**상태**: ✅ 가이드 작성 완료  
**다음 단계**: Cursor IDE 설정 확인 및 크레딧 충전

