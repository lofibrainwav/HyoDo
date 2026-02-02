# scripts/test_modular_architecture.py
import pathlib
import sys

# Ensure packages/afo-core is in python path
sys.path.append(pathlib.Path("packages/afo-core").resolve())


def test_modules() -> None:
    print("\n[Testing Modular Architecture]")

    try:
        # Import Strategists
        from strategists import jang_yeong_sil, shin_saimdang, yi_sun_sin

        print("✅ Imported Strategists (Jang Yeong-sil, Yi Sun-sin, Shin Saimdang)")

        # Import Tigers
        from tigers import guan_yu, huang_zhong, ma_chao, zhang_fei, zhao_yun

        print("✅ Imported Tigers (Guan Yu, Zhang Fei, Zhao Yun, Ma Chao, Huang Zhong)")

        # Test Strategists
        q_data = {
            "query": "Test",
            "context": {"valid_structure": True},
            "validation_level": 10,
            "narrative": "glassmorphism",
        }

        s1 = jang_yeong_sil.evaluate(q_data)
        s2 = yi_sun_sin.review(q_data)
        s3 = shin_saimdang.optimize(q_data)
        print(f"Strategists Output: Truth={s1}, Goodness={s2}, Beauty={s3}")

        # Test Tigers
        t1 = guan_yu.guard({"data": {"key": "val"}, "validation_level": 10})
        t2 = zhang_fei.gate(0.05, {"ethics_pass": True})
        t3 = zhao_yun.craft("<div>code</div>", 2)
        t4 = ma_chao.deploy({})
        t5 = huang_zhong.log("Test Action")

        print(
            f"Tigers Output:\n- Guan Yu: {t1}\n- Zhang Fei: {t2}\n- Zhao Yun: {t3}\n- Ma Chao: {t4}\n- Huang Zhong: {t5}"
        )

        print("🎉 Modular Architecture Verification Complete!")

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_modules()
