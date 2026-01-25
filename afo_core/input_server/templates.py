# Trinity Score: 95.0 (Phase 30 Templates Refactoring)
"""Input Server HTML Templates - Beauty-focused UI Components"""

from typing import Any


def get_home_template(
    success: str | None, error: str | None, api_keys: list[dict[str, Any]]
) -> str:
    """Generate home page HTML template with API key management interface.

    Args:
        success: Success message to display (optional)
        error: Error message to display (optional)
        api_keys: List of registered API keys

    Returns:
        Complete HTML page as string
    """
    # Generate API keys list HTML
    if api_keys:
        keys_html = "".join(
            [
                f"""
                <div class="key-item">
                    <div>
                        <div class="key-name">{key.get("name", "Unknown")}</div>
                        <div style="font-size: 12px; color: #999; margin-top: 4px;">
                            등록: {key.get("created_at", "Unknown")[:10]}
                        </div>
                    </div>
                    <div class="key-provider">{key.get("provider", "Unknown")}</div>
                </div>
                """
                for key in api_keys
            ]
        )
    else:
        keys_html = '<p style="color: #999; text-align: center;">아직 등록된 키가 없습니다</p>'

    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AFO Input Server - API 키 관리</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .header .organ {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        .form-group label {{
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        .form-group input,
        .form-group select,
        .form-group textarea {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }}
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .form-group .hint {{
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }}
        .submit-btn {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .submit-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }}
        .submit-btn:active {{
            transform: translateY(0);
        }}
        .message {{
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .message.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .message.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .key-list {{
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
        }}
        .key-list h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
        }}
        .key-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .key-item .key-name {{
            font-weight: 600;
            color: #333;
        }}
        .key-item .key-provider {{
            font-size: 12px;
            color: #666;
            background: white;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="organ">🍽️</div>
            <h1>AFO Input Server</h1>
            <p class="subtitle">胃 (Stomach) - API 키 입력 및 관리</p>
        </div>

        {'<div class="message success">✅ ' + success + "</div>" if success else ""}
        {'<div class="message error">❌ ' + error + "</div>" if error else ""}

        <!-- 탭 전환 버튼 -->
        <div style="display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0;">
            <button type="button" onclick="showForm('single')" id="tab-single" style="flex: 1; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600;">🔑 하나씩 입력</button>
            <button type="button" onclick="showForm('bulk')" id="tab-bulk" style="flex: 1; padding: 12px; background: #e0e0e0; color: #666; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600;">📋 대량 입력 (복붙)</button>
        </div>

        <!-- 하나씩 입력 폼 -->
        <div id="form-single">
        <form action="/add_key" method="post">
            <div class="form-group">
                <label for="name">API 키 이름 *</label>
                <input type="text" id="name" name="name" required placeholder="예: openai_primary">
                <div class="hint">영문, 숫자, 언더스코어만 사용 가능</div>
            </div>

            <div class="form-group">
                <label for="provider">제공자 *</label>
                <select id="provider" name="provider" required>
                    <option value="">-- 선택하세요 --</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="google">Google (Gemini)</option>
                    <option value="n8n">n8n</option>
                    <option value="github">GitHub</option>
                    <option value="other">기타</option>
                </select>
            </div>

            <div class="form-group">
                <label for="key">API 키 *</label>
                <textarea id="key" name="key" required placeholder="sk-..." rows="3"></textarea>
                <div class="hint">암호화되어 안전하게 저장됩니다 (AES-256)</div>
            </div>

            <div class="form-group">
                <label for="description">설명 (선택)</label>
                <input type="text" id="description" name="description" placeholder="예: 프로덕션 환경용">
            </div>

            <button type="submit" class="submit-btn">🔐 API 키 저장</button>
        </form>
        </div>

        <!-- 대량 입력 폼 -->
        <div id="form-bulk" style="display: none;">
        <form action="/bulk_import" method="post" onsubmit="return confirm('정말로 모든 API 키를 저장하시겠습니까?');">
            <div class="form-group">
                <label for="bulk_text">긴 문자열 복붙 (KEY=VALUE 형식) *</label>
                <textarea id="bulk_text" name="bulk_text" required placeholder="OPENAI_API_KEY=sk-proj-xxxxx&#10;ANTHROPIC_API_KEY=sk-ant-xxxxx&#10;N8N_URL=https://n8n.brnestrm.com&#10;API_YUNGDEOK=eyJhbGciOiJIUzI1NiIs...&#10;..." rows="15" style="font-family: monospace; font-size: 12px;"></textarea>
                <div class="hint">모든 환경 변수를 한 번에 복붙하세요. 자동으로 파싱하고 검증해서 저장합니다.</div>
            </div>
            <button type="submit" class="submit-btn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">🚀 대량 저장 시작</button>
        </form>
        </div>

        <script>
        function showForm(type) {{
            if (type === 'single') {{
                document.getElementById('form-single').style.display = 'block';
                document.getElementById('form-bulk').style.display = 'none';
                document.getElementById('tab-single').style.background = '#667eea';
                document.getElementById('tab-single').style.color = 'white';
                document.getElementById('tab-bulk').style.background = '#e0e0e0';
                document.getElementById('tab-bulk').style.color = '#666';
            }} else {{
                document.getElementById('form-single').style.display = 'none';
                document.getElementById('form-bulk').style.display = 'block';
                document.getElementById('tab-single').style.background = '#e0e0e0';
                document.getElementById('tab-single').style.color = '#666';
                document.getElementById('tab-bulk').style.background = '#667eea';
                document.getElementById('tab-bulk').style.color = 'white';
            }}
        }}
        </script>

        <div class="key-list">
            <h2>📋 등록된 API 키 ({len(api_keys)}개)</h2>
            {keys_html}
        </div>

        <div class="footer">
            <p>AFO Kingdom - 弘益人間 (Hongik Ingan)</p>
            <p style="margin-top: 5px;">眞善美孝 - Truth, Goodness, Beauty, Serenity</p>
        </div>
    </div>
</body>
</html>
    """
