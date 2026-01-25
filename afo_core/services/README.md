# AFO Core Services

This directory contains the core business logic and services of the AFO Kingdom backend.

## key Components

### Log Analysis Service
A resilient pipeline for processing and analyzing application logs.

- **Location**: `log_analysis.py`
- **Features**: Streaming, Caching, Plugins, Sequential Thinking.
- **Usage**:
  ```python
  from AFO.services.log_analysis import LogAnalysisService
  service = LogAnalysisService()
  service.run_pipeline("target.log")
  ```

### Plugin Manager
Handles dynamic loading of analysis plugins.

- **Location**: `plugin_manager.py`
- **Plugins Directory**: `plugins/`

## Testing

Run unit and integration tests:

```bash
# Unit Tests
pytest tests/services/test_plugin_manager.py

# Integration Tests
pytest tests/services/test_log_analysis_integration.py
```
