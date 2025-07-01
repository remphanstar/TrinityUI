"""
ComfyUI WebUI Installer for Project Trinity.

This module provides cross-platform installation and configuration for the ComfyUI
Stable Diffusion WebUI, including custom nodes and configuration files.

Author: ANXETY (original), Refactored for Trinity Project
License: MIT
"""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Setup project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Add project paths to Python path
for path in [PROJECT_ROOT, SCRIPTS_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Import Trinity modules
try:
    from modules.Manager import download_url_to_path
    import modules.json_utils as json_utils
except ImportError as e:
    logger.error(f"Failed to import Trinity modules: {e}")
    sys.exit(1)

# Configuration constants
UI_NAME = 'ComfyUI'
WEBUI_REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI_NAME}.zip"

# Environment paths helper functions
def get_environment_paths() -> dict[str, Path]:
    """Get environment paths from environment variables."""
    paths = {}
    for key, value in os.environ.items():
        if key.endswith('_path'):
            paths[key] = Path(value)
    return paths

def get_configuration_value(settings_path: Path, key: str, default: str) -> str:
    """Safely read configuration value with fallback."""
    if not settings_path.exists():
        logger.debug(f"Settings file {settings_path} not found, using default for {key}: {default}")
        return default
    try:
        return json_utils.read(settings_path, key)
    except Exception as e:
        logger.warning(f"Failed to read config key '{key}': {e}. Using default: {default}")
        return default

def change_directory(path: Path) -> None:
    """Change current working directory with error handling."""
    try:
        os.chdir(path)
        logger.debug(f"Changed directory to: {path}")
    except OSError as e:
        logger.error(f"Failed to change directory to {path}: {e}")
        raise

# Global paths configuration
PATHS = get_environment_paths()
HOME = PATHS.get('home_path', Path.cwd())
VENV = PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI = HOME / UI_NAME
CUSTOM_NODES_PATH = WEBUI / 'custom_nodes'
ENV_NAME = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.env_name', 'Colab')
FORK_REPO = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.fork', 'remphanostar/TrinityUI')
BRANCH = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.branch', 'main')

# Initialize home directory if it exists
if HOME.exists():
    change_directory(HOME)

# ==================== WEBUI OPERATIONS ====================

async def _download_file(url: str, directory: Path, filename: str) -> bool:
    """Download a single file with error handling."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as e:
            logger.warning(f"Could not delete existing file {file_path}: {e}")

    logger.info(f"Downloading {url} to {file_path}")
    success = download_url_to_path(url=url, target_full_path=str(file_path), log=True)
    if not success:
        logger.error(f"Error downloading {url} using download_url_to_path")
    return success


async def download_files(file_list: List[str]) -> None:
    """Download multiple files concurrently."""
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory_str = parts[1].strip() if len(parts) > 1 else str(WEBUI)
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        
        directory = Path(directory_str)
        tasks.append(_download_file(url, directory, filename))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_successful = True
    for i, result in enumerate(results):
        if isinstance(result, Exception) or result is False:
            logger.error(f"Download task failed for: {file_list[i]}. Exception/Result: {result}")
            all_successful = False
    
    if not all_successful:
        logger.error("One or more file downloads failed in download_files")


async def download_configuration() -> None:
    """Download configuration files and custom nodes."""
    logger.info("Downloading configuration files and custom nodes")
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    files_to_download = [
        f"{url_cfg}/{UI_NAME}/install-deps.py,{str(WEBUI)}",
        f"{url_cfg}/{UI_NAME}/comfy.settings.json,{str(WEBUI / 'user' / 'default')}",
        f"{url_cfg}/{UI_NAME}/Comfy-Manager/config.ini,{str(WEBUI / 'user' / 'default' / 'ComfyUI-Manager')}",
        f"{url_cfg}/{UI_NAME}/workflows/anxety-workflow.json,{str(WEBUI / 'user' / 'default' / 'workflows')}",
    ]
    
    # Create directories first
    for file_info in files_to_download:
        parts = file_info.split(',')
        directory = Path(parts[1].strip()) if len(parts) > 1 else WEBUI
        directory.mkdir(parents=True, exist_ok=True)
        
    await download_files(files_to_download)

    # Clone custom nodes
    extensions_list = [
        'https://github.com/Fannovel16/comfyui_controlnet_aux',
        'https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet',
        'https://github.com/hayden-fr/ComfyUI-Model-Manager',
        'https://github.com/jags111/efficiency-nodes-comfyui',
        'https://github.com/ltdrdata/ComfyUI-Impact-Pack',
        'https://github.com/ltdrdata/ComfyUI-Impact-Subpack',
        'https://github.com/ltdrdata/ComfyUI-Manager',
        'https://github.com/pythongosssss/ComfyUI-Custom-Scripts',
        'https://github.com/pythongosssss/ComfyUI-WD14-Tagger',
        'https://github.com/ssitu/ComfyUI_UltimateSDUpscale',
        'https://github.com/WASasquatch/was-node-suite-comfyui'
    ]

    CUSTOM_NODES_PATH.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    
    try:
        change_directory(CUSTOM_NODES_PATH)
        logger.info(f"Cloning custom nodes into {CUSTOM_NODES_PATH}")
        
        procs = []
        for command_str in extensions_list:
            parts = command_str.split()
            repo_url = parts[0]
            repo_name_git = repo_url.split('/')[-1]
            if repo_name_git.endswith('.git'):
                repo_name_git = repo_name_git[:-4]
            repo_name = parts[1] if len(parts) > 1 else repo_name_git

            if (CUSTOM_NODES_PATH / repo_name).exists():
                logger.info(f"Custom node '{repo_name}' already exists. Skipping clone.")
                continue
            
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {repo_url} {repo_name}",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            procs.append(process)
        
        results = await asyncio.gather(*[p.communicate() for p in procs], return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error cloning custom node (exception): {result}")
            elif procs[i].returncode != 0:
                stdout, stderr = result
                repo_name_failed = extensions_list[i].split('/')[-1].split()[0].replace('.git', '')
                logger.error(f"Error cloning custom node '{repo_name_failed}'. Git stderr: {stderr.decode() if stderr else 'No stderr'}")
                if stdout:
                    logger.error(f"Git stdout: {stdout.decode()}")
    finally:
        change_directory(original_cwd)

    # Run install dependencies script
    install_deps_script = WEBUI / "install-deps.py"
    if install_deps_script.exists():
        logger.info(f"Running downloaded {install_deps_script} (from __configs__)")
        
        # Cross-platform Python executable detection
        python_executable = None
        if sys.platform == "win32":
            python_executable = VENV / "Scripts" / "python.exe"
        else:
            python_executable = VENV / "bin" / "python"
        
        if not python_executable.exists():
            python_executable = Path(sys.executable)
        
        current_cwd = Path.cwd()
        try:
            change_directory(WEBUI)
            process = await asyncio.create_subprocess_exec(
                str(python_executable), str(install_deps_script),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"{install_deps_script} executed successfully")
                if stdout and stdout.decode().strip():
                    logger.info(f"Output:\n{stdout.decode().strip()}")
            else:
                logger.error(f"ERROR running {install_deps_script} (Return Code: {process.returncode})")
                if stdout and stdout.decode().strip():
                    logger.error(f"STDOUT:\n{stdout.decode().strip()}")
                if stderr and stderr.decode().strip():
                    logger.error(f"STDERR:\n{stderr.decode().strip()}")
        except Exception as e:
            logger.error(f"Exception running {install_deps_script}: {e}")
        finally:
            change_directory(current_cwd)
    else:
        logger.warning(f"{install_deps_script} (expected from __configs__) not found after download attempt")


def unpack_webui() -> None:
    """Download and extract the ComfyUI WebUI."""
    zip_path = HOME / f"{UI_NAME}.zip"
    logger.info(f"Step 1: Downloading WebUI from {WEBUI_REPO_URL}")
    
    download_successful = download_url_to_path(url=WEBUI_REPO_URL, target_full_path=str(zip_path), log=True)
    if not download_successful:
        logger.error(f"Download of {WEBUI_REPO_URL} failed. Cannot proceed.")
        sys.exit(1)
    
    logger.info(f"Step 2: Unzipping {zip_path} to {WEBUI}")
    WEBUI.mkdir(parents=True, exist_ok=True)
    
    potential_deps_script = WEBUI / "install-deps.py"
    if potential_deps_script.exists():
        logger.info(f"Removing potentially stale {potential_deps_script} before unzip")
        try:
            potential_deps_script.unlink()
        except OSError as e:
            logger.warning(f"Could not delete {potential_deps_script}: {e}")

    # Cross-platform unzip using Python zipfile module
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(WEBUI)
        logger.info(f"Successfully extracted {zip_path} to {WEBUI}")
    except Exception as e:
        logger.error(f"Error during unzip: {e}")
        sys.exit(1)

    logger.info(f"Step 3: Removing {zip_path}")
    try:
        zip_path.unlink()
        logger.info(f"Successfully removed {zip_path}")
    except Exception as e:
        logger.warning(f"Warning during zip removal: {e}")


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    logger.info(f"AnxLight {UI_NAME} UI Installer Script")
    unpack_webui()
    logger.info("Unpack finished, proceeding to download configuration & custom nodes")
    asyncio.run(download_configuration())
    logger.info("Script finished")