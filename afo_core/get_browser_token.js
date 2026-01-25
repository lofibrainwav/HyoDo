// 브라우저 콘솔에서 실행할 스크립트
// OpenAI 인증 토큰 추출

console.log("=== OpenAI 인증 토큰 추출 ===");

// 1. Cookies에서 찾기
const cookies = document.cookie.split(';').reduce((acc, cookie) => {
  const [key, value] = cookie.trim().split('=');
  acc[key] = value;
  return acc;
}, {});

console.log("\n📋 Cookies:");
Object.keys(cookies).forEach(key => {
  if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth') || key.toLowerCase().includes('session')) {
    console.log(`  ✅ ${key}: ${cookies[key].substring(0, 20)}...`);
  }
});

// 2. Local Storage에서 찾기
console.log("\n📋 Local Storage:");
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i);
  if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth') || key.toLowerCase().includes('session')) {
    console.log(`  ✅ ${key}: ${localStorage.getItem(key).substring(0, 20)}...`);
  }
}

// 3. Session Storage에서 찾기
console.log("\n📋 Session Storage:");
for (let i = 0; i < sessionStorage.length; i++) {
  const key = sessionStorage.key(i);
  if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth') || key.toLowerCase().includes('session')) {
    console.log(`  ✅ ${key}: ${sessionStorage.getItem(key).substring(0, 20)}...`);
  }
}

console.log("\n💡 위의 토큰 중 하나를 복사하여 API Wallet에 저장하세요.");
