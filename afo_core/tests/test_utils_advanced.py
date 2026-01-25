# Trinity Score: 90.0 (Established by Chancellor)
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add root directory to sys.path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from AFO.utils.cache_utils import CacheManager, cached
from AFO.utils.dry_run import DryRunMode, dry_run
from AFO.utils.framework_selector import FrameworkName, MissionProfile, select_framework


class TestCacheUtils(unittest.IsolatedAsyncioTestCase):
    @patch("redis.from_url")
    def test_cache_init_success(self, mock_redis_cls) -> None:
        """Test CacheManager initialization success"""
        mock_redis = MagicMock()
        mock_redis_cls.return_value = mock_redis

        cm = CacheManager()
        self.assertTrue(cm.enabled)
        mock_redis.ping.assert_called_once()

    @patch("redis.from_url")
    def test_cache_init_failure(self, mock_redis_cls) -> None:
        """Test CacheManager initialization failure"""
        mock_redis_cls.side_effect = Exception("Connection Error")

        cm = CacheManager()
        self.assertFalse(cm.enabled)
        self.assertIsNone(cm.redis)

    @patch("redis.from_url")
    def test_cache_operations(self, mock_redis_cls) -> None:
        """Test get/set/delete operations"""
        mock_redis = MagicMock()
        mock_redis_cls.return_value = mock_redis
        mock_redis.get.return_value = b'{"data": "value"}'
        mock_redis.delete.return_value = 1

        cm = CacheManager()

        # Test GET
        val = cm.get("key")
        self.assertEqual(val, {"data": "value"})

        # Test SET
        success = cm.set("key", {"data": "new"}, expire=60)
        self.assertTrue(success)
        mock_redis.setex.assert_called_with("key", 60, '{"data": "new"}')

        # Test DELETE
        deleted = cm.delete("key")
        self.assertTrue(deleted)

    @patch("AFO.utils.cache_utils.cache")
    async def test_cached_decorator(self, mock_cache_instance):
        """Test @cached decorator logic"""
        mock_cache_instance.get.return_value = None

        @cached(expire=10)
        async def my_func(a, b):
            return a + b

        # First call: cache miss
        res = await my_func(1, 2)
        self.assertEqual(res, 3)
        mock_cache_instance.set.assert_called()

        # Second call: cache hit
        mock_cache_instance.get.return_value = 3
        res2 = await my_func(1, 2)
        self.assertEqual(res2, 3)


class TestDryRun(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        DryRunMode.disable()

    def test_dry_run_toggle(self) -> None:
        """Test enable/disable toggle"""
        self.assertFalse(DryRunMode.is_enabled())
        DryRunMode.enable()
        self.assertTrue(DryRunMode.is_enabled())
        DryRunMode.disable()
        self.assertFalse(DryRunMode.is_enabled())

    async def test_dry_run_decorator_async(self):
        """Test decorator prevents execution in dry run mode"""

        @dry_run
        async def dangerous_op():
            return "DESTROYED"

        # Normal mode
        self.assertEqual(await dangerous_op(), "DESTROYED")

        # Dry Run mode
        DryRunMode.enable()
        result = await dangerous_op()
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("dry_run"))
        self.assertEqual(result.get("simulated_result"), "success")

    def test_dry_run_decorator_sync(self) -> None:
        """Test decorator for sync functions"""

        @dry_run
        def sync_op(x) -> None:
            return x * 2

        self.assertEqual(sync_op(5), 10)

        DryRunMode.enable()
        result = sync_op(5)
        self.assertTrue(result.get("dry_run"))


class TestFrameworkSelector(unittest.TestCase):
    def test_select_langgraph(self) -> None:
        """Complex + Reliable -> LangGraph"""
        p = MissionProfile(mission_type="coding", complexity=4, reliability=5)
        self.assertEqual(select_framework(p), FrameworkName.LANGGRAPH)

        p2 = MissionProfile(mission_type="coding", complexity=5, reliability=4)
        self.assertEqual(select_framework(p2), FrameworkName.LANGGRAPH)

    def test_select_autogen_research(self) -> None:
        """Research + Latency OK -> AutoGen"""
        p = MissionProfile(
            mission_type="research", complexity=3, reliability=3, latency_sensitivity=2
        )
        self.assertEqual(select_framework(p), FrameworkName.AUTOGEN)

    def test_select_crewai_cost(self) -> None:
        """Cost Sensitive -> CrewAI"""
        p = MissionProfile(mission_type="coding", complexity=3, reliability=3, cost_sensitivity=5)
        self.assertEqual(select_framework(p), FrameworkName.CREWAI)

    def test_select_crewai_simple(self) -> None:
        """Simple Task -> CrewAI"""
        p = MissionProfile(mission_type="chore", complexity=1, reliability=5)
        self.assertEqual(select_framework(p), FrameworkName.CREWAI)

    def test_default_autogen(self) -> None:
        """Balanced fallback"""
        p = MissionProfile(mission_type="coding", complexity=3, reliability=3, cost_sensitivity=3)
        self.assertEqual(select_framework(p), FrameworkName.AUTOGEN)


if __name__ == "__main__":
    unittest.main()
