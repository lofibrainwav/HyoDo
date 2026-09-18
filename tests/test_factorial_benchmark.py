from hyodo.factorial_benchmark import build_cases, run_benchmark


def test_m1_has_exactly_100_deterministic_cases() -> None:
    first = build_cases()
    second = build_cases()
    assert len(first) == 100
    assert first == second
    assert len({case.case_id for case in first}) == 100


def test_m1_positive_and_negative_controls_are_fail_closed() -> None:
    report = run_benchmark()
    assert report["case_count"] == 100
    assert report["status"] == "PASS"
    assert any(item["observed"] == "OBSERVED" for item in report["results"])
    assert any(item["observed"] == "UNOBSERVED" for item in report["results"])
    assert report["authority"] == "UNOBSERVED"


def test_authority_and_cross_lens_fields_are_not_decision_inputs() -> None:
    report = run_benchmark()
    assert all("decision" not in item for item in report["results"])
    assert all("score" not in item for item in report["results"])


def test_m1_uses_approved_strata_and_separate_metrics() -> None:
    report = run_benchmark()
    assert report["strata"] == {
        "single_factor": 60,
        "null_invariance": 20,
        "legitimate_dependency": 10,
        "residual_coverage": 10,
    }
    assert set(report["response_matrix"]) == {
        "truth",
        "goodness",
        "beauty",
        "benevolence",
        "hyo",
        "eternity",
    }
    assert report["metrics"]["legitimate_dependency"] == 10
    assert report["metrics"]["cross_lens_influence"] == "UNOBSERVED"
    assert report["metrics"]["taxonomy_incompleteness"] == 10
    assert all(item["contamination"] == "UNOBSERVED" for item in report["results"])
