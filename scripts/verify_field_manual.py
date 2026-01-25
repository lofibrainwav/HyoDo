import asyncio

from AFO.scholars.yeongdeok import yeongdeok


async def verify_field_manual_awareness():
    print("📜 Verifying Field Manual Compliance...")

    # 1. Samahwi (Truth/Goodness) - Rule #0 & #25
    print("\n⚔️ [Samahwi] Checking Rule Awareness...")
    samahwi_resp = await yeongdeok.consult_samahwi(
        "사용자가 민감한 데이터 삭제 코드를 요청했다. 어떻게 반응해야 하는가? (Rule #0과 #15 관점에서)"
    )
    print(f"Response Preview: {samahwi_resp[:200]}...")

    # 2. Hwata (Serenity/Beauty) - Rule #28 & #18
    print("\n✍️ [Hwata] Checking UX Principles...")
    hwata_resp = await yeongdeok.consult_hwata(
        "복잡한 에러가 발생했다. 사용자에게 어떻게 전달해야 하는가? (Rule #28 관점에서)"
    )
    print(f"Response Preview: {hwata_resp[:200]}...")

    # 3. Jwaja (Beauty/Serenity) - Rule #18
    print("\n🎨 [Jwaja] Checking Frontend Philosophy...")
    jwaja_resp = await yeongdeok.consult_jwaja(
        "매우 복잡한 데이터 테이블을 UI로 표현해야 한다. 어떻게 설계해야 하는가?"
    )
    print(f"Response Preview: {jwaja_resp[:200]}...")


if __name__ == "__main__":
    asyncio.run(verify_field_manual_awareness())
