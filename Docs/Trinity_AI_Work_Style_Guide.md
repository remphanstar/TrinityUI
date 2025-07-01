# AI Assistant Work Style Guide for Trinity Project

## 🚨 CRITICAL: TERMINAL COMMAND PROHIBITION

**NEVER USE TERMINAL COMMANDS** - They consistently hang and cause workflow interruptions.

### ❌ AVOID These Tools:
- `run_in_terminal` (causes hanging)
- Any PowerShell, bash, or command-line operations
- Git commands through terminal
- Package installation through terminal
- File operations through command line

### ✅ USE These Tools Instead:

#### File Operations
- `list_dir` - Explore directory structure
- `read_file` - Read existing files completely
- `create_file` - Create new files
- `insert_edit_into_file` - Add new code to existing files
- `replace_string_in_file` - Modify existing code

#### Code Validation
- `get_errors` - Validate syntax and imports (NOT terminal execution)
- `file_search` - Find files by pattern
- `grep_search` - Search within files

#### Analysis Tools
- `semantic_search` - Search codebase semantically
- `list_code_usages` - Find function/class usage

## 🎯 Preferred Workflow for Trinity

### 1. Repository Analysis
```
1. Use list_dir to understand structure
2. Use read_file to analyze existing code
3. Use file_search to locate specific files
4. Use grep_search to understand code patterns
```

### 2. Code Refactoring
```
1. Read entire file with read_file first
2. Plan changes based on full context
3. Use replace_string_in_file for targeted changes
4. Use insert_edit_into_file for new functionality
5. Validate with get_errors immediately after changes
```

### 3. Documentation Updates
```
1. Create new documentation with create_file
2. Update existing docs with replace_string_in_file
3. Keep documentation synchronized with code changes
4. No terminal-based documentation tools
```

### 4. Quality Assurance
```
1. Use get_errors for syntax validation
2. Read files to verify cross-module compatibility
3. Use semantic_search to find related code patterns
4. Document all changes in status files
```

## 🔧 Trinity-Specific Guidelines

### Core Module Refactoring Process
1. **Read Complete Module**: Use `read_file` for entire file
2. **Identify Patterns**: Use `grep_search` to find specific patterns
3. **Plan Refactoring**: Based on ReForge.py standards
4. **Apply Changes**: Use `replace_string_in_file` or `insert_edit_into_file`
5. **Validate**: Use `get_errors` to check syntax
6. **Document**: Update status files with changes

### File Management
- Use `list_dir` to identify temporary files
- Read files before deletion to ensure they're not needed
- Use direct file operations, never terminal commands
- Keep backups by reading original content

### Error Handling
- Use `get_errors` tool for validation
- Never execute code to test (causes hanging)
- Validate through static analysis only
- Document error handling improvements

## 📋 Quality Standards Reference

Use `scripts/UIs/ReForge.py` as the gold standard for:
- Code structure and organization
- Error handling patterns  
- Type hint usage
- Logging implementation
- Documentation style
- Input validation approaches

Apply these same patterns to all core modules:
- `modules/Manager.py`
- `modules/json_utils.py`
- `modules/TunnelHub.py`
- `modules/webui_utils.py`
- `modules/CivitaiAPI.py`

## 🎯 Success Metrics

- **No Terminal Usage**: 100% file operation tools
- **Complete File Reading**: Always read full context before changes
- **Immediate Validation**: Use get_errors after each significant change
- **Documentation Sync**: Update docs with every code change
- **Standards Compliance**: Match ReForge.py quality in all modules

---

**This workflow ensures efficient, non-blocking development while maintaining high code quality standards.**

---

## Current Progress & Issues (as of June 30, 2025)
*This section was appended by GitHub Copilot (chatGPT) for project status tracking.*

- **Notebook Refactor:** The TrinityUI notebook is now a robust, Colab-compatible, and user-friendly 3-cell notebook. Cell 1 (infrastructure) and Cell 2 (configuration hub) are production-ready, with improved debug UI, error handling, and output visibility. Cell 3 (asset download & WebUI launch) logic is correct, but cell content is currently corrupted and must be manually replaced with the provided working template.
- **Work Style Guide Compliance:** All recent code and documentation changes strictly follow the AI Work Style Guide: no terminal commands, all file operations via direct tools, and all code changes validated with get_errors. The debug workflow and documentation update process described in this guide have been followed for all recent changes.
- **Known Issues:**
  - Cell 3 notebook cell corruption (manual fix required).
  - Further UI/UX polish and documentation of known limitations is optional but recommended.
- **Next Steps:**
  - Finalize and commit the notebook filename change for clarity and repo tracking.
  - (Optional) Further polish UI/UX and document known limitations.
