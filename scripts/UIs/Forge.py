"""
Forge WebUI Installer for Project Trinity.

This module provides cross-platform installation and configuration for the Forge
Stable Diffusion WebUI, including extensions and configuration files.

Author: ANXETY (original), Refactored for Trinity Project
License: MIT
"""

import asyncio
import logging
import os
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import List

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
    import modules.json_utils as json_utils
except ImportError as e:
    logger.error(f"Failed to import Trinity modules: {e}")
    sys.exit(1)

# Configuration constants
UI_NAME = 'Forge'
FORGE_REPO_URL = "https://github.com/lllyasviel/stable-diffusion-webui-forge.git"

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
FORGE_EXTENSIONS_PATH = WEBUI / 'extensions'
ENV_NAME = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.env_name', 'Colab')
FORK_REPO = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.fork', 'remphanostar/TrinityUI')
BRANCH = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.branch', 'main')

# Initialize home directory if it exists
if HOME.exists():
    change_directory(HOME)

# ==================== WEBUI OPERATIONS ====================

async def _download_file(url: str, directory: Path, filename: str) -> None:
    """Cross-platform file download using urllib."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    
    if file_path.exists():
        file_path.unlink()  # Ensure fresh download for config files
    
    try:
        # Create SSL context that doesn't verify certificates for compatibility
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"Downloading {url} to {file_path}")
        urllib.request.urlretrieve(url, file_path)
        logger.info(f"Successfully downloaded {filename}")
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")


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
    await asyncio.gather(*tasks)


async def download_configuration() -> None:
    """Download configuration files and extensions."""
    logger.info("Downloading configuration files and extensions")
    
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    # Forge typically uses A1111's config files, or its own variants if specified in __configs__/Forge/
    configs_to_download = [
        f"{url_cfg}/styles.csv,{str(WEBUI)}",
        f"{url_cfg}/user.css,{str(WEBUI)}",
        f"{url_cfg}/card-no-preview.png,{str(WEBUI / 'html')}",
        f"{url_cfg}/notification.mp3,{str(WEBUI)}",
    ]
    
    # Ensure target directories for files exist
    for file_info in configs_to_download:
        parts = file_info.split(',')
        directory = Path(parts[1].strip()) if len(parts) > 1 else WEBUI
        directory.mkdir(parents=True, exist_ok=True)
    await download_files(configs_to_download)

    # Extension repositories (note: Forge has built-in ADetailer)
    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',
        'https://github.com/gutris1/sd-image-viewer Image-Viewer',
        'https://github.com/gutris1/sd-image-info Image-Info',
        'https://github.com/gutris1/sd-hub SD-Hub',
        'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    ]

    FORGE_EXTENSIONS_PATH.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    
    try:
        change_directory(FORGE_EXTENSIONS_PATH)
        logger.info(f"Cloning extensions into {FORGE_EXTENSIONS_PATH}")
        
        procs = []
        for command_str in extensions_list:
            parts = command_str.split()
            repo_url = parts[0]
            repo_name_git = repo_url.split('/')[-1]
            if repo_name_git.endswith('.git'):
                repo_name_git = repo_name_git[:-4]
            repo_name = parts[1] if len(parts) > 1 else repo_name_git
            
            if (FORGE_EXTENSIONS_PATH / repo_name).exists():
                logger.info(f"Extension '{repo_name}' already exists. Skipping clone.")
                continue

            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {repo_url} {repo_name}",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            procs.append(process)

        results = await asyncio.gather(*[p.communicate() for p in procs], return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error cloning extension (exception): {result}")
            elif procs[i].returncode != 0:
                stdout, stderr = result
                repo_name_failed = extensions_list[i].split('/')[-1].split()[0].replace('.git', '')
                logger.error(f"Error cloning extension '{repo_name_failed}'. Git stderr: {stderr.decode() if stderr else 'No stderr'}")
                if stdout:
                    logger.error(f"Git stdout: {stdout.decode()}")
    finally:
        change_directory(original_cwd)


def install_webui() -> None:
    """Clone or update the Forge WebUI repository."""
    logger.info(f"Step 1: Cloning/Verifying WebUI from {FORGE_REPO_URL} into {WEBUI}")
    
    if WEBUI.exists():
        logger.info(f"Directory {WEBUI} already exists. Assuming Forge is already cloned. Attempting to update...")
        original_cwd_git = Path.cwd()
        try:
            change_directory(WEBUI)
            # Attempt to update the repository if it already exists
            update_process = subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)
            logger.info(f"Forge repository updated successfully. Output: {update_process.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"'git pull' failed for existing Forge clone: {e.stderr}")
        except Exception as e:
            logger.warning(f"Failed to update existing Forge clone: {e}")
        finally:
            change_directory(original_cwd_git)
    else:
        try:
            subprocess.run(["git", "clone", FORGE_REPO_URL, str(WEBUI)], check=True)
            logger.info("Forge repository cloned successfully.")
        except Exception as e:
            logger.error(f"Error during git clone of Forge: {e}")
            sys.exit(1)

    logger.info("Forge repository is cloned/verified. Further setup is typically handled by Forge's own launch process.")


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    logger.info(f"AnxLight {UI_NAME} UI Installer Script")
    
    install_webui()
    logger.info("Forge repository clone/update process finished, proceeding to download configuration")
    asyncio.run(download_configuration())
    logger.info("Script finished")