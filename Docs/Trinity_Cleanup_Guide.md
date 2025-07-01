# Repository Cleanup Guide for Next AI Session

## � CRITICAL INSTRUCTION: NO TERMINAL COMMANDS
**The previous AI was instructed to avoid terminal commands as they hang and cause delays.**

Use these file operation tools instead:
- `list_dir` to identify files and directories
- Direct file deletion through file operations (not terminal `rm` or `Remove-Item`)
- `read_file` and `replace_string_in_file` for content management
- `create_file` for new files
- `get_errors` for validation (not terminal execution)

## 🗑️ Files to Remove (Using Direct Operations)

### Temporary Test Files
These files should be removed using direct file operations:
- `test_trinity.py` - Temporary test script
- `test_config.json` - Test configuration file

### Log Files  
- `trinity_execution.log` - Execution log file
- `trinity_unified.log` - Unified log file

### Auto-Generated Directories
Use `list_dir` to identify and remove these directories:
- `A1111/` - Auto1111 WebUI directory
- `Classic/` - Classic WebUI directory
- `ReForge/` - ReForge WebUI directory  
- `SD-UX/` - SD-UX WebUI directory
- `anxlight_venv/` - Virtual environment
- `trinity_venv/` - Trinity virtual environment
- `.gradio/` - Gradio cache directory

## ✅ Approach for Next AI Session

### Step 1: Repository Assessment (No Terminal)
```
1. Use list_dir to see current repository state
2. Use read_file to check existing files before removal
3. Identify temporary files and auto-generated content
4. Make cleanup decisions based on file analysis
```

### Step 2: Direct File Management
```
1. Remove files through file operations (not terminal commands)
2. Update .gitignore using replace_string_in_file if needed
3. Keep backups by reading content before major changes
4. Validate changes using get_errors tool
```

### Step 3: Core Module Refactoring (File-First Approach)
```
1. Read each core module completely with read_file
2. Apply refactoring using insert_edit_into_file and replace_string_in_file  
3. Validate with get_errors after each major change
4. Document changes in real-time using file operations
```

### Windows File Explorer
1. Navigate to the TrinityUI project directory
2. Delete the following items:
   - `test_trinity.py`
   - `test_config.json`  
   - `trinity_execution.log`
   - `trinity_unified.log`
   - `A1111/` folder
   - `Classic/` folder
   - `ReForge/` folder  
   - `SD-UX/` folder
   - `anxlight_venv/` folder
   - `trinity_venv/` folder
   - `.gradio/` folder
   - Any other auto-generated WebUI folders

### What the Repository Should Look Like After Cleanup

```
TrinityUI/
├── .git/                    # Keep - Git repository
├── .github/                 # Keep - GitHub configuration
├── .gitignore              # Keep - Git ignore rules
├── .vscode/                # Keep - VS Code settings
├── __configs__/            # Keep - Configuration templates
├── CSS/                    # Keep - Stylesheets
├── Docs/                   # Keep - Documentation
├── JS/                     # Keep - JavaScript files
├── modules/                # Keep - Core modules (NEEDS REFACTORING)
├── notebook/               # Keep - Jupyter notebook
├── scripts/                # Keep - Core scripts
├── README.md               # Keep - Project documentation
├── trinity_config.json     # Keep - Main configuration
├── package.json            # Keep - Node.js configuration
├── requirements.txt        # Keep - Python dependencies
└── ...other core files     # Keep - Essential project files
```

## 🎯 Post-Cleanup Status

After cleanup, the repository will be ready for:

1. **Core Module Refactoring** - Focus on `modules/` directory
2. **Standards Application** - Apply ReForge.py patterns to all core modules
3. **Error Validation** - Run error checking on refactored code
4. **Final Documentation** - Update all documentation with refactoring results

## ⚠️ Important Notes

- **DO NOT** delete anything in `modules/`, `scripts/UIs/`, `notebook/`, or `Docs/`
- **DO NOT** delete configuration files like `trinity_config.json`
- **DO NOT** delete any `.py` files in core directories
- **Keep** all files that are tracked in git (use `git status` to check)

The goal is to remove temporary files and auto-generated content while preserving all core project components that need to be refactored in the next phase.

---

## Cleanup Progress & Issues (as of June 30, 2025)
*This section was appended by GitHub Copilot (chatGPT) for project status tracking.*

- **Repository Cleanup:** All temporary test files, logs, and auto-generated directories have been identified and are being managed using direct file operations as outlined in this guide. No terminal commands have been used for cleanup, in strict compliance with project policy.
- **Notebook Artifacts:** Log files and test configs are now tracked and cleaned up as part of the notebook workflow. The .gitignore is up to date and excludes all non-core files.
- **Known Issues:**
  - Some log files (e.g., trinity_unified.log) may need periodic manual review and cleanup.
  - Notebook cell corruption (Cell 3) is a current issue, but does not affect repository cleanup.
- **Next Steps:**
  - Continue to use direct file operations for all cleanup tasks.
  - Review and update .gitignore as new auto-generated files appear.
