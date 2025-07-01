# scripts/manage_venvs.py (Matplotlib Fix + Aria2c Acceleration)
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
    Version: 1.0.0 - New function to inject matplotlib.use('Agg') fix into launch files
    Adds a matplotlib backend fix at the beginning of Python files to prevent backend conflicts
    """
    log_message(f"Injecting matplotlib backend fix...")
    
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
                
            # Prepare the fix
            fix_code = (
                "# Trinity matplotlib backend fix - MPLBACKEND=Agg\n"
                "import sys\n"
                "try:\n"
                "    import matplotlib\n"
                "    matplotlib.use('Agg')\n"
                "except ImportError:\n"
                "    pass\n\n"
            )
            
            # Find the right place to insert the code
            if content.startswith("#!/"):
                # Handle shebang - insert after it
                lines = content.splitlines()
                content = lines[0] + "\n" + fix_code + "\n".join(lines[1:])
            else:
                # Insert at the beginning
                content = fix_code + content
                
            # Write the modified content back to the file
            file_path.write_text(content, encoding='utf-8')
            log_message(f"✅ Successfully injected matplotlib fix into {launch_file}")
            
        except Exception as e:
            log_message(f"❌ Error injecting matplotlib fix into {launch_file}: {e}")

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
