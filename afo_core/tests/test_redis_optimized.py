# Trinity Score: 90.0 (Established by Chancellor)
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add root directory to sys.path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from AFO.utils.redis_optimized import OptimizedRedisCache


class TestOptimizedRedis(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock()
        # Mock register_script
        self.mock_script = AsyncMock()
        self.mock_client.register_script.return_value = self.mock_script

        self.cache = OptimizedRedisCache(client=self.mock_client)

    async def test_get_or_compute_hit(self):
        """Test Lua script returns hit"""
        # Lua returns ['hit', 'json_value']
        self.mock_script.return_value = ["hit", '{"val": 100}']

        async def compute():
            return 200

        result = await self.cache.get_or_compute("key", compute)
        self.assertEqual(result, {"val": 100})
        self.assertEqual(self.cache.hit_count, 1)

    async def test_get_or_compute_miss_compute(self):
        """Test Lua script returns miss, then compute and set"""
        # Lua returns ['miss', '']
        self.mock_script.return_value = ["miss", ""]

        # Mock setex (it's async in redis-py usually, but here client might be sync or async wrapper)
        # The code awaits client.setex, so we need AsyncMock for setex
        self.mock_client.setex = AsyncMock()

        async def compute():
            return 200

        result = await self.cache.get_or_compute("key", compute)
        self.assertEqual(result, 200)
        self.assertEqual(self.cache.miss_count, 1)
        self.mock_client.setex.assert_called_once()

    async def test_batch_get_success(self):
        """Test batch get with Lua"""
        # Lua returns list of stringified JSONs or False
        self.mock_script.return_value = ['{"a": 1}', False, '{"b": 2}']

        result = await self.cache.batch_get(["k1", "k2", "k3"])

        self.assertEqual(result["k1"], {"a": 1})
        self.assertIsNone(result["k2"])
        self.assertEqual(result["k3"], {"b": 2})

    async def test_batch_set_pipeline(self):
        """Test batch set uses pipeline"""
        # pipeline() context manager
        mock_pipe = AsyncMock()
        self.mock_client.pipeline.return_value.__aenter__.return_value = mock_pipe

        await self.cache.batch_set({"k1": 1, "k2": 2}, ttl_seconds=60)

        self.assertEqual(mock_pipe.setex.call_count, 2)
        mock_pipe.execute.assert_called_once()
        self.assertEqual(self.cache.pipeline_count, 1)

    def test_stats(self) -> None:
        """Test stats calculation"""
        self.cache.hit_count = 80
        self.cache.miss_count = 20

        stats = self.cache.get_stats()
        self.assertEqual(stats["hit_rate"], 0.8)
        self.assertEqual(stats["total_requests"], 100)


if __name__ == "__main__":
    unittest.main()
