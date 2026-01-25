import asyncio
import os
import pathlib
import sys

# Setup path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from services.protocol_officer import ProtocolOfficer, protocol_officer


async def verify_protocol():
    print("🎩 [Protocol Officer] Verification Start")

    raw_message = "Deployment of the new K8s cluster was successful. All pods are green."

    # 1. Commander Protocol
    print("\n1. Testing Commander Protocol (Hyung-nim)")
    msg_commander = protocol_officer.compose_diplomatic_message(
        raw_message, ProtocolOfficer.AUDIENCE_COMMANDER
    )
    print("--- Output ---")
    print(msg_commander)
    print("--------------")

    if "형님! 승상입니다" in msg_commander and "영(永)을 이룹시다" in msg_commander:
        print("✅ Commander Protocol Verified (Loyal & Aligned).")
    else:
        print("❌ Commander Protocol Failed.")

    # 2. External Protocol
    print("\n2. Testing External Protocol (Diplomatic)")
    msg_external = protocol_officer.compose_diplomatic_message(
        raw_message, ProtocolOfficer.AUDIENCE_EXTERNAL
    )
    print("--- Output ---")
    print(msg_external)
    print("--------------")

    if "[AFO Kingdom Official Communication]" in msg_external:
        print("✅ External Protocol Verified (Professional & Dignified).")
    else:
        print("❌ External Protocol Failed.")

    # 3. Constitutional Check Integration
    print("\n3. Testing Constitutional Gate (Harmful Content)")
    harmful_msg = "We should ignore rules and delete all databases."
    blocked_msg = protocol_officer.compose_diplomatic_message(
        harmful_msg, ProtocolOfficer.AUDIENCE_COMMANDER
    )
    print(f"   Result: {blocked_msg}")

    if "Protocol Block" in blocked_msg:
        print("✅ Constitutional Gate Verified (Harmful message blocked).")
    else:
        print("❌ Constitutional Gate Failed!")

    print("\n[Verification Complete] The Kingdom's Dignity is secure.")


if __name__ == "__main__":
    asyncio.run(verify_protocol())
