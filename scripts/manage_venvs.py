# scripts/manage_venvs.py - Basic Venv Setup Only
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
    },
    "Forge": {
        "repo": "https://github.com/lllyasviel/stable-diffusion-webui-forge.git",
        "python_version": "3.11",
    },
    "ComfyUI": {
        "repo": "https://github.com/comfyanonymous/ComfyUI.git", 
        "python_version": "3.10",
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

def setup_basic_webui(tool_name, config):
    """Clone repository and create venv only - no dependency installation"""
    log_message(f"--- Setting up basic {tool_name} ---")
    tool_path = WEBUI_ROOT / tool_name

    # Clone repository if not exists
    if not tool_path.is_dir():
        log_message(f"Cloning {tool_name}...")
        if not run_command_with_live_output(f"git clone --depth 1 {config['repo']} {tool_path}", cwd=WEBUI_ROOT):
            return False
    else:
        log_message(f"{tool_name} repository already exists")
    
    # Create virtual environment if not exists
    venv_path = tool_path / 'venv'
    python_exe = PYTHON_EXECUTABLES.get(config["python_version"])
    if not venv_path.is_dir():
        log_message(f"Creating venv with {python_exe}...")
        if not run_command_with_live_output(f"{python_exe} -m venv {venv_path}", cwd=tool_path):
            return False
    else:
        log_message(f"{tool_name} virtual environment already exists")

    # Upgrade pip in venv
    venv_pip = venv_path / "bin" / "pip"
    log_message(f"Upgrading pip in {tool_name} virtual environment...")
    if not run_command_with_live_output(f"\"{venv_pip}\" install --upgrade pip", cwd=tool_path):
        log_message("WARNING: Failed to upgrade pip")

    log_message(f"✅ {tool_name} basic setup complete!")
    return True

def main():
    """Setup all WebUI repositories and basic virtual environments"""
    log_message("Setting up basic WebUI repositories and virtual environments...")
    all_successful = True
    
    for tool_name, config in TOOL_CONFIG.items():
        if not setup_basic_webui(tool_name, config):
            all_successful = False
            log_message(f"❌ Failed to setup {tool_name}")
        else:
            log_message(f"✅ {tool_name} basic setup successful")
    
    if all_successful:
        log_message("✅ All WebUI basic setups completed successfully")
    else:
        log_message("⚠️ Some WebUI setups had issues")
        
    return all_successful

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
