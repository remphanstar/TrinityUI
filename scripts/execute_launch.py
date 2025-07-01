# scripts/execute_launch.py - Final Path Fix Version
import os
import sys
import json
import subprocess
import shlex
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# --- Setup and Helpers ---
def get_project_root():
    """
    Gets the project root directory. Prioritizes the environment variable
    set by Cell 1 for maximum reliability.
    """
    # --- THIS IS THE FIX ---
    # Prioritize the environment variable set by the main notebook cells.
    env_root = os.environ.get('TRINITY_PROJECT_ROOT')
    if env_root and Path(env_root).exists():
        return Path(env_root)
    
    # Fallback for direct execution or if env var is missing
    current = Path.cwd()
    if (current / 'scripts').exists():
        return current
    if (current.parent / 'scripts').exists():
        return current.parent
    return Path.cwd() # Last resort

def detect_environment():
    if 'COLAB_GPU' in os.environ: return 'colab'
    return 'windows' if os.name == 'nt' else 'linux'

PROJECT_ROOT = get_project_root()
WEBUI_ROOT = Path('/content')
TRINITY_VERSION = "1.3.3" # Version bump for path fix
CONFIG_PATH = PROJECT_ROOT / "trinity_config.json"
LOG_FILE = PROJECT_ROOT / "trinity_unified.log"
ENV_TYPE = detect_environment()

def log_to_unified(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [v{TRINITY_VERSION}] [{level}] [EXECUTION] {message}\n"
    print(f"[{level}] {message}")
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f: f.write(log_entry)
    except: pass

def load_config() -> Dict[str, Any]:
    # This will now correctly look in /content/TrinityUI/trinity_config.json
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f: return json.load(f)

def construct_launch_command(config: Dict[str, Any]) -> list:
    """Constructs the launch command using the correct venv."""
    webui_choice = config.get("webui_choice", "A1111")
    webui_path = WEBUI_ROOT / webui_choice
    venv_path = webui_path / 'venv'
    
    venv_python = venv_path / 'bin' / 'python'
    if not venv_python.exists():
        log_to_unified(f"Venv Python not found at {venv_python}!", "ERROR")
        return None

    args = [str(venv_python), "launch.py"]
    
    custom_args_str = config.get("custom_args", "")
    if custom_args_str:
        args.extend(shlex.split(custom_args_str))
        
    tunnel = config.get("tunnel_choice", "Gradio")
    if tunnel == "Gradio" and '--share' not in args:
        args.append('--share')
    
    if '--xformers' not in args:
        args.append('--xformers')
    
    return args

def launch_webui(config: Dict[str, Any]) -> bool:
    """Launches the selected WebUI with a corrected environment for matplotlib."""
    webui_choice = config.get("webui_choice", "A1111")
    webui_path = WEBUI_ROOT / webui_choice

    if not webui_path.exists():
        log_to_unified(f"WebUI path not found: {webui_path}", "ERROR")
        return False

    command_list = construct_launch_command(config)
    if not command_list:
        return False

    log_to_unified(f"Executing command: {' '.join(command_list)}", "SUCCESS")
    print("\n" + "="*50 + f"\n🚀 LAUNCHING {webui_choice} FROM ITS VENV...\n" + "="*50)

    try:
        launch_env = os.environ.copy()
        launch_env["MPLBACKEND"] = "Agg"

        process = subprocess.Popen(
            command_list,
            cwd=webui_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=launch_env
        )

        for line in iter(process.stdout.readline, ''):
            sys.stdout.write(line)
            sys.stdout.flush()
        
        return_code = process.wait()
        if return_code != 0:
            log_to_unified(f"{webui_choice} exited with error code {return_code}.", "ERROR")
            return False
        return True

    except KeyboardInterrupt:
        log_to_unified("Launch interrupted by user.", "INFO")
        return True
    except Exception as e:
        log_to_unified(f"Launch failed with an exception: {e}", "ERROR")
        return False

def main():
    try:
        log_to_unified("=== Trinity Venv-Aware Execution Engine Started ===")
        config = load_config()
        if not config: return False
        
        # Asset download is now part of the setup cell
        
        if not launch_webui(config):
            log_to_unified("WebUI launch failed.", "ERROR")
            return False
            
        return True
    except Exception as e:
        log_to_unified(f"Critical execution failure: {e}", "ERROR")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
