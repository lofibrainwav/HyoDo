import asyncio
import logging

from AFO.llms.cli_wrapper import CLIWrapper

# Config Logging
logging.basicConfig(level=logging.DEBUG)


async def test():
    print("Testing Claude CLI...")
    if CLIWrapper.is_available("claude"):
        res = await CLIWrapper.execute_claude("What is 1+1?")
        print(f"Claude Result: {res}")
    else:
        print("Claude CLI not found.")

    print("\nTesting Codex CLI...")
    if CLIWrapper.is_available("codex"):
        res = await CLIWrapper.execute_codex("What is 1+1?")
        print(f"Codex Result: {res}")
    else:
        print("Codex CLI not found.")


if __name__ == "__main__":
    asyncio.run(test())
