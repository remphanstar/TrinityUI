"""
SD-UX WebUI Installer for Project Trinity.

This module provides cross-platform installation and configuration for the SD-UX
WebUI. Note: The exact nature and preferred installation method of "SD-UX" should be verified.
This script currently assumes installation from the ANXETY HF archive (zip file).

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
import zipfile
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
    from modules.Manager import m_download
    import modules.json_utils as json_utils
except ImportError as e:
    logger.error(f"Failed to import Trinity modules: {e}")
    sys.exit(1)

# Configuration constants
UI_NAME = 'SD-UX'
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
EXTS_PATH = WEBUI / 'extensions'
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
        file_path.unlink()
    
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
        directory = Path(parts[1].strip()) if len(parts) > 1 else WEBUI
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        tasks.append(_download_file(url, directory, filename))
    await asyncio.gather(*tasks)


async def download_configuration() -> None:
    """Download generic configuration files (review for SD-UX compatibility)."""
    logger.info("Downloading generic configuration files (review for SD-UX compatibility)")
    
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    configs_to_download = [
        f"{url_cfg}/styles.csv,{WEBUI}",
        f"{url_cfg}/user.css,{WEBUI}",
        f"{url_cfg}/card-no-preview.png,{WEBUI}/html",
        f"{url_cfg}/notification.mp3,{WEBUI}",
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(configs_to_download)
    logger.info("Generic extension download step skipped/placeholder for SD-UX. Needs verification.")


def unpack_webui() -> None:
    """Download and extract the SD-UX WebUI."""
    zip_path = HOME / f"{UI_NAME}.zip"
    logger.info(f"Step 1: Downloading WebUI from {WEBUI_REPO_URL} (assuming zip archive)")
    
    m_download(f"{WEBUI_REPO_URL} {str(HOME)} {UI_NAME}.zip", log=True)
    
    logger.info(f"Step 2: Unzipping {zip_path} to {WEBUI}")
    WEBUI.mkdir(parents=True, exist_ok=True)
    
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
    
    logger.info("Basic unzip complete. If this is Stability-AI/StableStudio, further Node.js/Yarn setup is needed.")


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    logger.info(f"AnxLight {UI_NAME} UI Installer Script")
    logger.info(f"Note: Installation method and nature of '{UI_NAME}' needs verification.")
    
    unpack_webui()
    logger.info("Unpack process finished.")
    asyncio.run(download_configuration())
    logger.info("Script finished")