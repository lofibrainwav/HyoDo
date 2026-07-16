#!/usr/bin/env python3
"""
TICKET-046     

    →     .
"""

import asyncio
import sys
from pathlib import Path

#   Python  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

from validation.ast_analyzer import analyze_code
from validation.logger import log_result

#   
TEST_CODE_GOOD = """
def calculate_sum(a, b):
    '''   .'''
    return a + b

def multiply(a, b):
    '''   .'''
    return a * b

#  
if __name__ == "__main__":
    result = calculate_sum(1, 2)
    print(f"Sum: {result}")
""".lstrip()

def calculate_sum(a, b):
    x = 1/0  # ZeroDivisionError
    return a + b + not_defined

#  
import os
def dangerous_cmd(cmd):
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=False).returncode  #  

#  assert
assert True  #   

#   
try:
    risky_operation()
except:  # bare except
    pass
""".lstrip()


async def main():
    """  """
    print("=" * 60)
    print("TICKET-046     ")
    print("=" * 60)

    #   
    print("\n🔍    ...")

    try:
        # AST  
        result = analyze_code(TEST_CODE_GOOD)
        print(f"✅ AST  : score={result['score']:.2f}, approved={result['approved']}")
        print(f"    : {len(result['structure']['functions'])}")
        print(f"    : {len(result['vulnerabilities'])}")

        #   
        log_result({"ticket": "TICKET-046", "test": "ast_analysis_success", "result": result})
        print("✅   ")

    except Exception as e:
        print(f"❌  : {e}")
        return

    print("\n🎯 TICKET-046     !")
    print("SOLID  , AST  , Trinity Score  ")


if __name__ == "__main__":
    asyncio.run(main())
