# Trinity Score: 95.0 (Phase 29B API Compatibility Layer Functional Tests)


def test_compat_facade() -> None:
    """Verify HTMLDataFacade in api/compat.py."""
    from api.compat import HTMLDataFacade

    facade = HTMLDataFacade()

    # Trigger all data provider methods
    assert facade.get_philosophy_data() is not None
    assert facade.get_port_data() is not None
    assert facade.get_personas_data() is not None
    assert facade.get_royal_rules_data() is not None
    assert facade.get_architecture_data() is not None
    assert facade.get_stats_data() is not None


def test_compat_convenience_funcs() -> None:
    """Verify convenience functions in api/compat.py."""
    from api.compat import (
        calculate_trinity,
        get_personas_list,
        get_philosophy_pillars,
        get_project_stats,
        get_royal_constitution,
        get_service_ports,
        get_system_architecture,
    )

    assert get_philosophy_pillars() is not None
    assert get_service_ports() is not None
    assert get_personas_list() is not None
    assert get_royal_constitution() is not None
    assert get_system_architecture() is not None
    assert get_project_stats() is not None

    # Trinity calculation
    scores = {"truth": 90, "goodness": 90, "beauty": 90, "serenity": 90, "eternity": 90}
    result = calculate_trinity(scores)
    assert 85 <= result <= 95
