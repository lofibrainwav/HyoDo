"""
AFO Kingdom Plugin Manager
Trinity Score: 眞 (Truth) - Dynamic Loading & Integration
Author: AFO Kingdom Development Team
"""

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path

# Use structured logger if available
try:
    from AFO.utils.structured_logger import StructuredLogger

    logger = StructuredLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

from AFO.services.plugins.base import LogAnalysisPlugin


class PluginManager:
    """
    Manages loading and execution of Log Analysis Plugins.
    Scans the `plugins` directory for compatible plugin implementations.
    """

    def __init__(self, plugin_dir: str | None = None) -> None:
        if plugin_dir:
            self.plugin_dir = Path(plugin_dir)
        else:
            # Default to 'plugins' subdirectory of services
            self.plugin_dir = Path(__file__).resolve().parent / "plugins"

        self.plugins: dict[str, LogAnalysisPlugin] = {}
        self.load_plugins()

    def load_plugins(self) -> None:
        """Dynamically discover and load plugins from the plugin directory"""
        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return

        logger.info("Loading plugins...", context={"plugin_dir": str(self.plugin_dir)})

        # Walk through modules in the plugin directory
        for _, name, _ in pkgutil.iter_modules([str(self.plugin_dir)]):
            try:
                # Import module dynamically (e.g. AFO.services.plugins.my_plugin)
                # Assuming standard package structure; adjustment might be needed based on exact path
                module_name = f"AFO.services.plugins.{name}"

                try:
                    module = importlib.import_module(module_name)
                except ImportError:
                    # Fallback for direct loading if package path fails
                    spec = importlib.util.spec_from_file_location(
                        name, self.plugin_dir / f"{name}.py"
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    else:
                        continue

                # Inspect module for Plugin classes
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, LogAnalysisPlugin)
                        and obj is not LogAnalysisPlugin
                    ):
                        try:
                            plugin_instance = obj()
                            self.plugins[plugin_instance.name] = plugin_instance
                            logger.info(f"Loaded plugin: {plugin_instance.name}")
                        except Exception as e:
                            logger.error(f"Failed to instantiate plugin {obj.__name__}: {e}")

            except Exception as e:
                logger.error(f"Error loading plugin module {name}: {e}")

    def get_plugin(self, name: str) -> LogAnalysisPlugin | None:
        return self.plugins.get(name)

    def get_all_plugins(self) -> list[LogAnalysisPlugin]:
        return list(self.plugins.values())
