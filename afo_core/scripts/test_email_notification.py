#!/usr/bin/env python3
"""
Email Notification Test Script
이메일 알림 시스템 테스트 스크립트

Usage:
    python test_email_notification.py [--send-test]

Options:
    --send-test    Actually send a test email (requires SMTP config)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.mirror.models import TrinityScoreAlert
from scripts.mirror.notifiers import EmailNotifier


def test_email_notifier_instantiation() -> bool:
    """Test 1: EmailNotifier can be instantiated"""
    print("\n🧪 Test 1: EmailNotifier Instantiation")
    try:
        notifier = EmailNotifier()
        print(f"   ✅ Instantiated successfully")
        print(f"   📧 SMTP Host: {notifier.smtp_host or 'Not configured'}")
        print(f"   📧 SMTP Port: {notifier.smtp_port}")
        print(f"   📧 From: {notifier.from_addr or 'Not configured'}")
        print(
            f"   📧 To: {', '.join(notifier.to_addrs) if notifier.to_addrs else 'Not configured'}"
        )
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_email_notifier_with_env() -> bool:
    """Test 2: EmailNotifier reads from environment"""
    print("\n🧪 Test 2: Environment Variable Reading")
    try:
        # Set test environment variables
        os.environ["IRS_EMAIL_SMTP_HOST"] = "smtp.test.com"
        os.environ["IRS_EMAIL_SMTP_PORT"] = "465"
        os.environ["IRS_EMAIL_SMTP_USER"] = "test@example.com"
        os.environ["IRS_EMAIL_SMTP_PASSWORD"] = "testpassword"
        os.environ["IRS_EMAIL_FROM"] = "alerts@example.com"
        os.environ["IRS_EMAIL_TO"] = "admin1@example.com,admin2@example.com"

        notifier = EmailNotifier()

        assert notifier.smtp_host == "smtp.test.com", "SMTP host mismatch"
        assert notifier.smtp_port == 465, "SMTP port mismatch"
        assert notifier.smtp_user == "test@example.com", "SMTP user mismatch"
        assert notifier.from_addr == "alerts@example.com", "From address mismatch"
        assert notifier.to_addrs == ["admin1@example.com", "admin2@example.com"], (
            "To addresses mismatch"
        )

        print(f"   ✅ All environment variables read correctly")
        print(f"   📧 Multiple recipients: {len(notifier.to_addrs)} addresses")

        # Cleanup
        for key in [
            "IRS_EMAIL_SMTP_HOST",
            "IRS_EMAIL_SMTP_PORT",
            "IRS_EMAIL_SMTP_USER",
            "IRS_EMAIL_SMTP_PASSWORD",
            "IRS_EMAIL_FROM",
            "IRS_EMAIL_TO",
        ]:
            del os.environ[key]

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_email_content_formatting() -> bool:
    """Test 3: Email content formatting"""
    print("\n🧪 Test 3: Email Content Formatting")
    try:
        alert = TrinityScoreAlert(
            pillar="truth",
            score=85.5,
            threshold=90.0,
            timestamp="2026-02-15T12:00:00",
            message="Test alert: Truth pillar score below threshold",
        )

        notifier = EmailNotifier()
        content = notifier._format_email_content(alert, is_critical=False)

        assert "subject" in content, "Missing subject"
        assert "text" in content, "Missing text body"
        assert "html" in content, "Missing HTML body"
        assert "TRUTH" in content["subject"].upper(), "Subject doesn't contain pillar"
        assert "⚠️" in content["subject"] or "WARNING" in content["subject"], (
            "Missing warning indicator"
        )

        print(f"   ✅ Subject: {content['subject'][:60]}...")
        print(f"   ✅ Text body length: {len(content['text'])} chars")
        print(f"   ✅ HTML body length: {len(content['html'])} chars")
        print(f"   ✅ Contains HTML tags: {'<html>' in content['html']}")

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_critical_email_formatting() -> bool:
    """Test 4: Critical email formatting"""
    print("\n🧪 Test 4: Critical Alert Formatting")
    try:
        alert = TrinityScoreAlert(
            pillar="total",
            score=75.0,
            threshold=90.0,
            timestamp="2026-02-15T12:00:00",
            message="CRITICAL: Total Trinity Score below acceptable threshold",
        )

        notifier = EmailNotifier()
        content = notifier._format_email_content(alert, is_critical=True)

        assert "CRITICAL" in content["subject"], "Missing CRITICAL indicator"
        assert "🚨" in content["subject"], "Missing critical emoji"
        assert "#B71C1C" in content["html"], "Wrong critical color in HTML"

        print(f"   ✅ Subject: {content['subject']}")
        print(f"   ✅ Critical styling applied")

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_email_send_without_config() -> bool:
    """Test 5: Email send gracefully handles missing config"""
    print("\n🧪 Test 5: Graceful Handling of Missing Config")
    try:
        # Ensure no email config is set
        for key in [
            "IRS_EMAIL_SMTP_HOST",
            "IRS_EMAIL_SMTP_USER",
            "IRS_EMAIL_SMTP_PASSWORD",
            "IRS_EMAIL_FROM",
            "IRS_EMAIL_TO",
        ]:
            if key in os.environ:
                del os.environ[key]

        alert = TrinityScoreAlert(
            pillar="goodness",
            score=88.0,
            threshold=90.0,
            timestamp="2026-02-15T12:00:00",
            message="Test alert without config",
        )

        notifier = EmailNotifier()
        result = await notifier.send(alert, is_critical=False)

        # Should return False gracefully when not configured
        assert result == False, "Should return False when not configured"

        print(f"   ✅ Gracefully skipped (not configured)")
        print(f"   ✅ Return value: {result}")

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def run_all_tests() -> dict[str, bool]:
    """Run all tests"""
    print("=" * 60)
    print("📧 AFO Kingdom Email Notification Test Suite")
    print("=" * 60)

    results = {}

    results["instantiation"] = test_email_notifier_instantiation()
    results["env_reading"] = test_email_notifier_with_env()
    results["content_formatting"] = test_email_content_formatting()
    results["critical_formatting"] = test_critical_email_formatting()
    results["send_without_config"] = await test_email_send_without_config()

    return results


def print_summary(results: dict[str, bool]) -> None:
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n   Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Email notification system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")

    return passed == total


async def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test email notification system")
    parser.add_argument(
        "--send-test",
        action="store_true",
        help="Actually send a test email (requires SMTP configuration)",
    )
    args = parser.parse_args()

    results = await run_all_tests()
    success = print_summary(results)

    if args.send_test:
        print("\n" + "=" * 60)
        print("📧 Sending Real Test Email")
        print("=" * 60)

        if not all(
            [
                os.environ.get("IRS_EMAIL_SMTP_HOST"),
                os.environ.get("IRS_EMAIL_SMTP_USER"),
                os.environ.get("IRS_EMAIL_SMTP_PASSWORD"),
                os.environ.get("IRS_EMAIL_TO"),
            ]
        ):
            print("❌ Cannot send test email: SMTP configuration not found in environment")
            print("   Please set: IRS_EMAIL_SMTP_HOST, IRS_EMAIL_SMTP_USER,")
            print("               IRS_EMAIL_SMTP_PASSWORD, IRS_EMAIL_TO")
            return 1

        alert = TrinityScoreAlert(
            pillar="test",
            score=95.0,
            threshold=90.0,
            timestamp="2026-02-15T12:00:00",
            message="This is a test email from AFO Kingdom Guardian",
        )

        notifier = EmailNotifier()
        result = await notifier.send(alert, is_critical=False)

        if result:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email")
            return 1

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
