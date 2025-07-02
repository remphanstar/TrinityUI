# scripts/manage_venvs.py (Matplotlib Fix + Aria2c Acceleration) - CORRECTED VERSION
import os
import sys
import subprocess
import json
import re
from pathlib import Path

PROJECT_ROOT = Path.cwd()
WEBUI_ROOT = Path('/content')
PIP_CACHE_DIR = WEBUI_ROOT / '.pip_cache'
PIP_CACHE_DIR.mkdir(exist_ok=True)

PYTHON_EXECUTABLES = {
    "3.10": "/usr/bin/python3.10",
    "3.11": "/usr/bin/python3.11",
}

TOOL_CONFIG = {
    "A1111": {
        "repo": "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git",
        "python_version": "3.10",
        "reqs_file": "requirements_versions.txt",
        "post_install": [
            "pip install numpy==1.26.4",
            "pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121",
            "pip install xformers==0.0.23.post1 --index-url https://download.pytorch.org/whl/cu121",
        ],
        "launch_files": ["launch.py", "webui.py"],
    },
    "Forge": {
        "repo": "https://github.com/lllyasviel/stable-diffusion-webui-forge.git",
        "python_version": "3.11",
        "reqs_file": "requirements_versions.txt",
        "post_install": [
            "pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cu121",
            "pip install xformers"
        ],
        "launch_files": ["launch.py", "webui.py"],
    },
    "ComfyUI": {
        "repo": "https://github.com/comfyanonymous/ComfyUI.git", 
        "python_version": "3.10",
        "reqs_file": "requirements.txt",
        "post_install": [
            "pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121",
            "pip install xformers==0.0.23.post1 --index-url https://download.pytorch.org/whl/cu121",
        ],
        "launch_files": ["main.py"],
    },
}

def log_message(message):
    print(f"[VenvManager] {message}")

def run_command_with_live_output(command, cwd):
    log_message(f"Executing: {command}")
    try:
        process = subprocess.Popen(
            command, shell=True, cwd=cwd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8',
            errors='replace', bufsize=1
        )
        for line in iter(process.stdout.readline, ''):
            print(f"  > {line.strip()}")
        return process.wait() == 0
    except Exception as e:
        log_message(f"❌ Command exception: {e}")
        return False

def fast_pip_install(venv_pip_path, requirements_file_path, cwd):
    log_message("Phase 1: Calculating dependencies...")
    pip_resolve_cmd = f"\"{venv_pip_path}\" install --dry-run --report - -r \"{requirements_file_path}\""
    result = subprocess.run(pip_resolve_cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        log_message(f"❌ Failed to resolve dependencies. Check pip version. Stderr: {result.stderr}")
        log_message("Falling back to standard (slower) pip install...")
        return run_command_with_live_output(f"\"{venv_pip_path}\" install -r \"{requirements_file_path}\"", cwd=cwd)
        
    try:
        report = json.loads(result.stdout)
        urls_to_download = [part['download_info']['url'] for part in report.get('install', [])]
    except Exception as e:
        log_message(f"❌ Failed to parse pip report. Falling back. Error: {e}")
        return run_command_with_live_output(f"\"{venv_pip_path}\" install -r \"{requirements_file_path}\"", cwd=cwd)

    if urls_to_download:
        log_message(f"Phase 2: Downloading {len(urls_to_download)} packages with aria2c...")
        url_file = PIP_CACHE_DIR / "urls.txt"
        url_file.write_text("\n".join(urls_to_download))
        aria_cmd = f"aria2c -c -x 16 -s 16 -k 1M -j $(nproc) --dir=\"{PIP_CACHE_DIR}\" -i \"{url_file}\""
        if not run_command_with_live_output(aria_cmd, cwd=PROJECT_ROOT):
            log_message("❌ aria2c download failed. Falling back.")
            return run_command_with_live_output(f"\"{venv_pip_path}\" install -r \"{requirements_file_path}\"", cwd=cwd)
    
    log_message("Phase 3: Installing packages from local cache...")
    pip_offline_cmd = f"\"{venv_pip_path}\" install --no-index --find-links=\"{PIP_CACHE_DIR}\" -r \"{requirements_file_path}\""
    return run_command_with_live_output(pip_offline_cmd, cwd=cwd)

def inject_matplotlib_fix(tool_path, launch_files):
    """
    Version: 2.0.0 - CORRECTED matplotlib fix injection that properly handles from __future__ imports
    Adds a matplotlib backend fix at the correct position in Python files to prevent backend conflicts
    """
    log_message(f"Injecting matplotlib backend fix...")
    
    fix_code = (
        "# Trinity matplotlib backend fix - MPLBACKEND=Agg\n"
        "import os\n"
        "os.environ['MPLBACKEND'] = 'Agg'\n"
        "try:\n"
        "    import matplotlib\n"
        "    matplotlib.use('Agg')\n"
        "except ImportError:\n"
        "    pass\n"
    )
    
    for launch_file in launch_files:
        file_path = tool_path / launch_file
        if not file_path.exists():
            log_message(f"Warning: Launch file {launch_file} not found, skipping matplotlib fix")
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if fix is already applied
            if "matplotlib.use('Agg')" in content:
                log_message(f"Matplotlib fix already present in {launch_file}")
                continue
            
            lines = content.splitlines()
            insert_position = 0
            
            # Find the correct insertion point
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip shebang
                if stripped.startswith('#!'):
                    insert_position = i + 1
                    continue
                
                # Skip initial comments and docstrings
                if (stripped.startswith('#') or 
                    stripped.startswith('"""') or 
                    stripped.startswith("'''") or
                    stripped == ""):
                    insert_position = i + 1
                    continue
                
                # Handle future imports - they MUST come first after shebang/comments
                if stripped.startswith('from __future__ import'):
                    insert_position = i + 1
                    continue
                
                # Stop at first non-future import or actual code
                break
            
            # Insert the matplotlib fix at the correct position
            fix_lines = fix_code.strip().split('\n')
            
            # Add empty line before fix if needed for readability
            if insert_position < len(lines) and lines[insert_position].strip() != "":
                fix_lines.append("")
            
            # Insert fix lines at the correct position
            for i, fix_line in enumerate(fix_lines):
                lines.insert(insert_position + i, fix_line)
            
            # Write back to file
            new_content = '\n'.join(lines)
            file_path.write_text(new_content, encoding='utf-8')
            log_message(f"✅ Successfully injected matplotlib fix into {launch_file} at position {insert_position + 1}")
            
        except Exception as e:
            log_message(f"❌ Error injecting matplotlib fix into {launch_file}: {e}")
            # Try to clean up any broken fix
            try:
                content = file_path.read_text(encoding='utf-8')
                # Remove any existing Trinity matplotlib fix that might be broken
                lines = content.splitlines()
                clean_lines = []
                skip_next = False
                
                for line in lines:
                    if "Trinity matplotlib backend fix" in line:
                        skip_next = True
                        continue
                    if skip_next and any(x in line for x in ["import os", "matplotlib", "os.environ", "except", "pass"]):
                        continue
                    if skip_next and line.strip() and not any(x in line for x in ["import", "os.environ", "matplotlib", "except", "pass"]):
                        skip_next = False
                    
                    if not skip_next:
                        clean_lines.append(line)
                
                file_path.write_text('\n'.join(clean_lines), encoding='utf-8')
                log_message(f"🔧 Cleaned up broken matplotlib fix in {launch_file}")
            except:
                log_message(f"❌ Could not clean up {launch_file}")

def setup_tool(tool_name, config):
    log_message(f"--- Setting up {tool_name} ---")
    tool_path = WEBUI_ROOT / tool_name

    if not tool_path.is_dir():
        log_message(f"Cloning {tool_name}...")
        if not run_command_with_live_output(f"git clone --depth 1 {config['repo']} {tool_path}", cwd=WEBUI_ROOT):
            return False
    
    venv_path = tool_path / 'venv'
    python_exe = PYTHON_EXECUTABLES.get(config["python_version"])
    if not venv_path.is_dir():
        log_message(f"Creating venv with {python_exe}...")
        if not run_command_with_live_output(f"{python_exe} -m venv {venv_path}", cwd=tool_path):
            return False

    # Upgrade pip inside the newly created venv
    venv_pip = venv_path / "bin" / "pip"
    log_message("Upgrading pip in virtual environment...")
    if not run_command_with_live_output(f"\"{venv_pip}\" install --upgrade pip", cwd=tool_path):
        log_message("WARNING: Failed to upgrade pip. High-speed install may fail.")
    
    # Now that pip is upgraded, the high-speed install will work.
    reqs_file_path = tool_path / config['reqs_file']
    if reqs_file_path.exists():
        if not fast_pip_install(venv_pip, reqs_file_path, cwd=tool_path):
             return False
    
    if "post_install" in config:
        log_message("Running post-install compatibility fixes...")
        for cmd in config['post_install']:
            full_cmd = cmd.replace("pip", str(venv_pip))
            if not run_command_with_live_output(full_cmd, cwd=tool_path):
                return False
    
    # Apply matplotlib backend fix to launch files
    if "launch_files" in config:
        inject_matplotlib_fix(tool_path, config["launch_files"])
    else:
        log_message("No launch files specified for matplotlib fix")

    log_message(f"✅ {tool_name} setup complete!")
    return True

def main():
    all_successful = True
    for tool_name, config in TOOL_CONFIG.items():
        if not setup_tool(tool_name, config):
            all_successful = False
            break
    if not all_successful:
        sys.exit(1)

if __name__ == "__main__":
    main()
