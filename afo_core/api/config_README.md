# AFO.api.config Module

## Overview

The `config.py` module handles FastAPI application configuration and lifespan management. It implements the 眞 (Truth) principle through type-safe configuration and the 孝 (Serenity) principle through proper lifecycle management.

## Key Components

### `get_app_config() -> FastAPI`

Creates and configures the FastAPI application instance.

**Features:**
- OpenAPI metadata configuration
- Lifespan manager setup
- Type-safe configuration validation

**Usage:**
```python
from AFO.api.config import get_app_config

app = get_app_config()
# Returns fully configured FastAPI application
```

### `get_server_config() -> tuple[str, int]`

Retrieves server host and port configuration from environment or settings.

**Environment Variables:**
- `API_SERVER_HOST`: Server bind host (default: "0.0.0.0")
- `API_SERVER_PORT`: Server bind port (default: 8010)

**Returns:**
- Tuple of (host: str, port: int)

### `get_lifespan_manager() -> AsyncContextManager`

Creates the application lifespan context manager for startup and shutdown operations.

**Lifespan Events:**
- **Startup**: Calls `initialize_system()` from `AFO.api.initialization`
- **Shutdown**: Calls `cleanup_system()` from `AFO.api.cleanup`

**Error Handling:**
- Startup failures are re-raised (critical)
- Cleanup failures are logged but don't prevent shutdown

## Configuration Flow

```
Environment Variables
        ↓
   get_settings_safe()
        ↓
  get_server_config()
        ↓
  get_app_config()
        ↓
Lifespan Manager (startup/cleanup)
```

## Dependencies

- `fastapi.FastAPI`: Core web framework
- `AFO.api.metadata.get_api_metadata()`: OpenAPI configuration
- `AFO.api.initialization.initialize_system()`: Startup logic
- `AFO.api.cleanup.cleanup_system()`: Shutdown logic

## Error Scenarios

### Settings Unavailable
```python
# If get_settings_safe() returns None
# Falls back to environment variables
# Defaults to localhost:8010
```

### Initialization Failure
```python
# Critical startup errors are re-raised
# Application fails to start
# Detailed error logging provided
```

### Cleanup Failure
```python
# Cleanup errors are logged but not re-raised
# Application shutdown continues
# Prevents masking of startup errors
```

## Testing

### Unit Tests
```python
def test_get_app_config():
    app = get_app_config()
    assert app.title == "AFO Kingdom Soul Engine API"
    assert app.version == "6.3.0"

def test_get_server_config():
    host, port = get_server_config()
    assert isinstance(host, str)
    assert isinstance(port, int)
    assert port > 0
```

### Integration Tests
```python
async def test_lifespan_manager():
    async with get_lifespan_manager():
        # System should be initialized
        pass
    # System should be cleaned up
```

## Monitoring

### Health Checks
The configuration module enables health monitoring through lifespan management. The system health can be verified via:

- `/health`: Basic connectivity
- `/api/health/comprehensive`: Detailed system status

### Logging
Configuration operations are logged with appropriate levels:
- `INFO`: Successful configuration
- `WARNING`: Fallback configurations used
- `ERROR`: Configuration failures

## Security Considerations

- Server binding defaults to `0.0.0.0` (all interfaces) for development
- Production deployments should restrict to specific interfaces
- Environment variables take precedence over defaults
- No sensitive data stored in configuration (handled by settings module)

## Performance Impact

- Minimal startup overhead (< 100ms)
- Lifespan operations are async and non-blocking
- Configuration is cached after first access
- No runtime performance impact

## Future Enhancements

### Planned Features
- Dynamic configuration reloading
- Configuration validation schemas
- Multi-environment configuration profiles
- Configuration hot-swapping

### API Evolution
- Backward compatible configuration changes
- Deprecation warnings for old environment variables
- Migration guides for configuration updates

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8010
   # Change port via environment
   export API_SERVER_PORT=8011
   ```

2. **Configuration Not Loading**
   ```python
   # Debug configuration
   from AFO.api.compat import get_settings_safe
   settings = get_settings_safe()
   print(f"Settings loaded: {settings is not None}")
   ```

3. **Lifespan Errors**
   ```python
   # Test lifespan components individually
   from AFO.api.initialization import initialize_system
   await initialize_system()  # Should not raise
   ```

### Debug Commands
```bash
# Check configuration
python -c "from AFO.api.config import get_server_config; print(get_server_config())"

# Test app creation
python -c "from AFO.api.config import get_app_config; app = get_app_config(); print(f'App: {app.title}')"
```

## Related Modules

- `AFO.api.metadata`: OpenAPI specification
- `AFO.api.initialization`: Startup logic
- `AFO.api.cleanup`: Shutdown logic
- `AFO.api.compat`: Settings and compatibility
