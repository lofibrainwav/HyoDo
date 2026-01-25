# AFO Kingdom API Module Documentation

## Overview

The `AFO.api` module provides a comprehensive FastAPI-based web framework for the AFO Kingdom Soul Engine. This module implements the 眞善美孝永 (Truth, Goodness, Beauty, Serenity, Eternity) philosophy through modular, scalable API architecture.

## Architecture

```
AFO.api/
├── config.py          # FastAPI app configuration & lifespan management
├── metadata.py        # OpenAPI metadata & documentation
├── middleware.py      # CORS, security, monitoring middleware
├── routers.py         # Centralized router registration system
├── initialization.py  # System component initialization
├── cleanup.py         # System cleanup & resource management
├── compat.py          # Strangler fig pattern for legacy compatibility
└── routers/           # Individual router implementations
    ├── skills.py      # Skills registry API
    └── ...
```

## Core Principles

### 眞 (Truth) - Technical Accuracy
- Type-safe configurations with Pydantic validation
- Comprehensive error handling and logging
- Automated testing and validation

### 善 (Goodness) - Reliability & Safety
- Graceful degradation on component failures
- Resource cleanup and connection pooling
- Security-first middleware implementation

### 美 (Beauty) - Elegance & Maintainability
- Modular architecture with clear separation of concerns
- Consistent naming conventions and patterns
- Comprehensive documentation

### 孝 (Serenity) - Operational Excellence
- Automated initialization and cleanup
- Health monitoring and alerting
- Performance optimization

### 永 (Eternity) - Long-term Viability
- Versioned APIs with backward compatibility
- Extensible architecture for future phases
- Comprehensive logging and auditing

## Module Reference

### `config.py` - Application Configuration

**Purpose**: FastAPI application creation and lifespan management

**Key Functions**:
- `get_app_config()`: Create configured FastAPI application
- `get_server_config()`: Get host/port configuration
- `get_lifespan_manager()`: Async context manager for app lifecycle

**Usage**:
```python
from AFO.api.config import get_app_config

app = get_app_config()
# FastAPI app with proper configuration and lifespan
```

### `metadata.py` - OpenAPI Documentation

**Purpose**: API documentation and OpenAPI specification

**Key Functions**:
- `get_api_metadata()`: Get complete OpenAPI metadata
- `get_api_tags()`: Get endpoint categorization tags

**Features**:
- Comprehensive API description
- Tagged endpoint organization
- Version and contact information

### `middleware.py` - Middleware Stack

**Purpose**: Cross-cutting concerns and request processing

**Key Functions**:
- `setup_middleware(app)`: Configure all middleware

**Middleware Included**:
- CORS for cross-origin requests
- Security auditing and logging
- Prometheus metrics collection

### `routers.py` - Router Registration

**Purpose**: Centralized API router management

**Key Functions**:
- `setup_routers(app)`: Register all API routers

**Router Categories**:
- Core system routers (health, root)
- Feature routers (pillars, trinity, skills)
- Phase-specific routers (budget, AICPA, learning pipelines)

### `initialization.py` - System Startup

**Purpose**: Component initialization during application startup

**Key Functions**:
- `initialize_system()`: Initialize all system components

**Initialization Sequence**:
1. Query expansion setup
2. AntiGravity controls
3. RAG engines initialization
4. Skills registry loading
5. Yeongdeok memory system
6. Strategy engine compilation
7. Database connections
8. LLM client setup

### `cleanup.py` - System Shutdown

**Purpose**: Resource cleanup during application shutdown

**Key Functions**:
- `cleanup_system()`: Cleanup all system components

**Cleanup Operations**:
- Yeongdeok browser session cleanup
- Database connection pool closure
- Redis connection cleanup

### `compat.py` - Compatibility Layer

**Purpose**: Strangler fig pattern for gradual migration

**Key Features**:
- Conditional imports with fallbacks
- Legacy system compatibility
- Safe import handling

## Usage Examples

### Basic Application Setup

```python
from AFO.api.config import get_app_config
from AFO.api.middleware import setup_middleware
from AFO.api.routers import setup_routers

# Create FastAPI app
app = get_app_config()

# Setup middleware
setup_middleware(app)

# Register all routers
setup_routers(app)

# App is ready to serve
```

### Custom Router Addition

```python
from AFO.api.routers import setup_routers
from fastapi import APIRouter

# Create custom router
custom_router = APIRouter()

@custom_router.get("/custom")
async def custom_endpoint():
    return {"message": "Custom endpoint"}

# Setup all routers (custom router will be added automatically
# if placed in AFO.api.routers module)
setup_routers(app)
```

### Health Monitoring

```python
from AFO.api.initialization import initialize_system
from AFO.api.cleanup import cleanup_system

# Initialize system
await initialize_system()

# ... application logic ...

# Cleanup on shutdown
await cleanup_system()
```

## Configuration

### Environment Variables

- `API_SERVER_HOST`: Server bind host (default: 0.0.0.0)
- `API_SERVER_PORT`: Server bind port (default: 8010)
- `POSTGRES_HOST`: PostgreSQL host
- `POSTGRES_PORT`: PostgreSQL port
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port

### Settings

Uses Pydantic-based settings with environment variable override capability:

```python
from AFO.api.compat import get_settings_safe

settings = get_settings_safe()
if settings:
    db_host = settings.POSTGRES_HOST
    # ... other settings
```

## Testing

### Unit Tests

Each module includes comprehensive unit tests:

```bash
# Run all API tests
pytest packages/afo-core/tests/api/

# Run specific module tests
pytest packages/afo-core/tests/api/test_config.py
```

### Integration Tests

System-wide integration testing:

```bash
# Run integration test suite
python scripts/integration_test.py
```

## Monitoring & Observability

### Health Endpoints

- `GET /health`: Basic health check
- `GET /api/health/comprehensive`: Detailed system health
- `GET /api/5pillars/current`: Trinity score monitoring

### Metrics

- Prometheus metrics exposed on port 8001
- Request latency and error rates
- Database connection pool status
- Memory usage and performance metrics

### Logging

Comprehensive logging with structured output:
- Request/response logging
- Error tracking with context
- Performance monitoring
- Audit trails for security events

## Security

### Authentication & Authorization

- JWT-based authentication system
- Role-based access control (RBAC)
- API key management through wallet system

### Security Middleware

- Request validation and sanitization
- Rate limiting and DDoS protection
- Audit logging for compliance
- Secure headers and CORS policies

## Performance Optimization

### Caching Strategy

- Redis-based caching for frequently accessed data
- Cache invalidation with TTL policies
- Cache warming for critical endpoints

### Database Optimization

- Connection pooling with PostgreSQL
- Query optimization and indexing
- Asynchronous database operations

### Async/Await Patterns

- Full async/await implementation
- Concurrent request handling
- Non-blocking I/O operations

## Deployment

### Docker Configuration

```dockerfile
FROM python:3.12-slim

COPY packages/afo-core/ /app/
WORKDIR /app

RUN pip install -e .
EXPOSE 8010

CMD ["python", "api_server.py"]
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Database connections verified
- [ ] Redis cache available
- [ ] External API keys configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring and alerting setup
- [ ] Load balancer configuration
- [ ] Backup and recovery procedures

## Troubleshooting

### Common Issues

1. **Router Not Found**: Check import paths in compat.py
2. **Database Connection Failed**: Verify environment variables
3. **Import Errors**: Ensure all dependencies installed
4. **Middleware Issues**: Check middleware configuration order

### Debug Commands

```bash
# Check router registration
python scripts/debug_router_registration.py

# Run integration tests
python scripts/integration_test.py

# Check system health
curl http://localhost:8010/api/health/comprehensive
```

## Future Enhancements

### Phase Roadmap

- **Phase 28**: Advanced caching strategies
- **Phase 29**: GraphQL API support
- **Phase 30**: Real-time WebSocket integration
- **Phase 31**: Advanced security features
- **Phase 32**: Multi-region deployment support

### API Evolution

- Semantic versioning for backward compatibility
- Deprecation warnings for legacy endpoints
- Gradual migration paths for breaking changes
- Feature flags for experimental features

---

## Contributing

When adding new routers or middleware:

1. Follow the established patterns in existing modules
2. Add comprehensive unit tests
3. Update this documentation
4. Ensure backward compatibility
5. Test integration with existing components

## License

This module is part of the AFO Kingdom project and follows the same licensing terms.
