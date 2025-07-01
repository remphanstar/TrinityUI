# Trinity Core Module Refactoring Guide

## 📋 Overview
This document provides specific guidance for refactoring Trinity's core modules to match the professional standards established in `scripts/UIs/ReForge.py`.

## 🎯 Gold Standard Reference
**Primary Reference**: `scripts/UIs/ReForge.py`
- Complete implementation of all coding standards
- Custom exception hierarchy
- Dataclass configuration patterns
- Context managers for resource handling
- Comprehensive error handling
- Async/await patterns
- Input validation and sanitization

## 🔧 Core Modules Analysis

### 1. modules/Manager.py (Priority: CRITICAL)
**Current Issues Identified:**
- Legacy code patterns with minimal error handling
- No type hints
- Inconsistent logging
- Global variables and mutable state
- Mixed responsibility (download + config + asset management)

**Refactoring Requirements:**
```python
# Required imports to add
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any
from pathlib import Path
import logging
from contextlib import contextmanager

# Custom exceptions needed
class ManagerError(Exception): pass
class DownloadError(ManagerError): pass
class AssetValidationError(ManagerError): pass
class ConfigurationError(ManagerError): pass

# Configuration dataclass pattern
@dataclass(frozen=True)
class DownloadConfig:
    civitai_token: Optional[str] = None
    huggingface_token: Optional[str] = None
    max_retries: int = 3
    timeout: int = 300
    chunk_size: int = 1024 * 1024  # 1MB
```

**Key Functions to Refactor:**
- `clean_url()` - Add comprehensive URL validation
- `download_url_to_path()` - Implement retry logic and better error handling
- `m_download()` - Restructure with proper async patterns
- `download_selected_assets()` - Add progress tracking and validation

### 2. modules/json_utils.py (Priority: HIGH)
**Expected Issues:**
- Basic JSON read/write without validation
- No schema validation
- Limited error handling

**Refactoring Pattern:**
```python
from typing import Any, Dict, Optional, Union, TypeVar
from pathlib import Path
import json
from dataclasses import dataclass

T = TypeVar('T')

class JsonUtilsError(Exception): pass
class ValidationError(JsonUtilsError): pass
class SchemaError(JsonUtilsError): pass

@dataclass(frozen=True)
class JsonConfig:
    validate_schema: bool = True
    create_backup: bool = True
    encoding: str = 'utf-8'
    indent: int = 2
```

### 3. modules/TunnelHub.py (Priority: MEDIUM)
**Expected Patterns Needed:**
- Network security validation
- Connection pooling
- Proper timeout handling
- SSL context management

**Security Considerations:**
```python
import ssl
from urllib.parse import urlparse
from contextlib import asynccontextmanager

class TunnelError(Exception): pass
class SecurityError(TunnelError): pass
class ConnectionError(TunnelError): pass

@dataclass(frozen=True)
class TunnelConfig:
    ssl_verify: bool = True
    timeout: int = 30
    max_connections: int = 10
    retry_attempts: int = 3
```

### 4. modules/webui_utils.py (Priority: MEDIUM)
**Expected Structure:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class WebUIType(Enum):
    A1111 = "A1111"
    CLASSIC = "Classic"
    COMFYUI = "ComfyUI"
    FORGE = "Forge"
    REFORGE = "ReForge"
    SD_UX = "SD-UX"

@dataclass(frozen=True)
class WebUIConfig:
    ui_type: WebUIType
    repo_url: str
    branch: str = "main"
    extensions: List[str] = None
```

### 5. modules/CivitaiAPI.py (Priority: MEDIUM)
**API Client Patterns:**
```python
import aiohttp
from dataclasses import dataclass
from typing import Optional, Dict, Any

class CivitaiError(Exception): pass
class APIRateLimitError(CivitaiError): pass
class AuthenticationError(CivitaiError): pass

@dataclass(frozen=True)
class CivitaiConfig:
    api_token: Optional[str] = None
    base_url: str = "https://civitai.com/api/v1"
    rate_limit: int = 100  # requests per minute
    timeout: int = 30
```

## 🛠️ Implementation Strategy

### ⚠️ CRITICAL: Development Approach
**NEVER USE TERMINAL COMMANDS** - They hang and cause delays. Always use direct file operations:
- `read_file` to analyze existing code
- `replace_string_in_file` or `insert_edit_into_file` to make changes
- `get_errors` to validate syntax and imports
- `create_file` for new files or complete rewrites
- `list_dir` to explore file structure

### Phase 1: Structure & Types (Direct File Editing)
1. Read existing module with `read_file` (full file)
2. Add comprehensive imports using `replace_string_in_file`
3. Define custom exception hierarchies with `insert_edit_into_file`
4. Create configuration dataclasses using direct editing
5. Add type hints to all functions through targeted replacements

### Phase 2: Error Handling (File-by-File Approach)
1. Replace generic `except Exception` with specific types (direct editing)
2. Add input validation at function entry points
3. Implement proper logging with structured messages
4. Add context managers for resource management (direct file operations)

### Phase 3: Architecture (Direct Refactoring)
1. Separate concerns into focused functions using file editing
2. Implement async patterns where beneficial (direct code changes)
3. Add retry mechanisms for network operations  
4. Create validation functions for data integrity

### Phase 4: Documentation & Testing (No Terminal)
1. Add comprehensive docstrings using `replace_string_in_file`
2. Document exception cases and error conditions
3. Add usage examples in docstrings
4. Validate with `get_errors` tool (not terminal execution)

## 📏 Code Quality Checklist

For each module, ensure:

### ✅ Structure
- [ ] All imports properly organized (stdlib, third-party, local)
- [ ] Custom exception hierarchy defined
- [ ] Configuration dataclasses created
- [ ] Type hints on all functions and parameters
- [ ] Proper module-level docstring

### ✅ Error Handling  
- [ ] Specific exception types (no bare `except Exception`)
- [ ] Input validation at function boundaries
- [ ] Proper error propagation with context
- [ ] Resource cleanup in finally blocks or context managers
- [ ] Meaningful error messages with context

### ✅ Logging
- [ ] Structured logging with appropriate levels
- [ ] Debug information for troubleshooting
- [ ] Error context included in log messages
- [ ] No print statements (use logging)

### ✅ Async Patterns
- [ ] Async functions where I/O is involved
- [ ] Proper await usage
- [ ] asyncio.gather for concurrent operations
- [ ] Timeout handling for network operations

### ✅ Documentation
- [ ] Comprehensive docstrings with Args, Returns, Raises
- [ ] Usage examples where helpful
- [ ] Type information clearly documented
- [ ] Edge cases and limitations noted

## 🎯 Success Metrics

### Quantitative Goals
- **Type Coverage**: >95% of functions have complete type hints
- **Error Handling**: 100% of functions have specific exception handling
- **Documentation**: All public functions have comprehensive docstrings
- **Logging**: Structured logging throughout with no print statements

### Qualitative Goals
- **Maintainability**: Code is self-documenting and easy to understand
- **Reliability**: Robust error handling prevents crashes
- **Testability**: Functions are focused and testable
- **Performance**: Efficient patterns with async where appropriate

## 🔗 Cross-Module Dependencies

### Import Relationships
```
Manager.py -> json_utils.py, webui_utils.py, CivitaiAPI.py
TunnelHub.py -> webui_utils.py
webui_utils.py -> json_utils.py
CivitaiAPI.py -> (external APIs only)
json_utils.py -> (no internal dependencies)
```

### Refactoring Order
1. **json_utils.py** (foundation - no dependencies)
2. **CivitaiAPI.py** (isolated API client)
3. **webui_utils.py** (depends on json_utils)
4. **TunnelHub.py** (depends on webui_utils)
5. **Manager.py** (depends on all others)

---

**Use this guide as a reference when refactoring each core module to ensure consistency and quality across the entire codebase.**

---

## Current Progress & Issues (as of June 30, 2025)
*This section was appended by GitHub Copilot (chatGPT) for project status tracking.*

- **Notebook Refactor:** The TrinityUI notebook is now a robust, Colab-compatible, and user-friendly 3-cell notebook:
  - **Cell 1:** Infrastructure setup and debug UI (production-ready, robust, improved error handling and output visibility).
  - **Cell 2:** Configuration hub and Gradio interface (production-ready, robust, improved status display, prevents duplicate UI).
  - **Cell 3:** Asset download and WebUI launch (logic is correct, but cell content is currently corrupted and must be manually replaced with the provided working template).
- **UI/UX:** Major improvements to CSS/JS asset loading, debug interface, and output visibility. All outputs are robust and user-friendly.
- **Logging & Error Handling:** Logging is now robust, with errors visible in both logs and UI. Log sync to JavaScript is protected against crashes.
- **Colab Compatibility:** Addressed port conflicts, subprocess handling, memory management, and path issues for Colab environments.
- **Known Issues:**
  - Cell 3 content is corrupted and must be manually replaced with the working template (provided in project notes).
  - Further UI/UX polish and documentation of known limitations is optional but recommended.
- **Next Steps:**
  - Finalize and commit the notebook filename change for clarity and repo tracking.
  - (Optional) Further polish UI/UX and document known limitations.

---

## Core Module Refactoring Progress & Issues (as of June 30, 2025)
*This section was appended by GitHub Copilot (chatGPT) for project status tracking.*

- **Refactoring Status:** All core modules (Manager.py, json_utils.py, etc.) remain compliant with the patterns and standards described in this guide. The notebook now uses these refactored modules for asset management and WebUI launching.
- **Integration:** The 3-cell notebook structure has improved separation of concerns, making it easier to maintain and refactor core modules independently.
- **Known Issues:**
  - No new issues in core modules, but Cell 3 notebook corruption is an open issue (not related to module code).
- **Next Steps:**
  - Continue to refactor and validate core modules as notebook features expand.
  - Document any new patterns or exceptions as they arise.
