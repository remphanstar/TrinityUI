"""
AUTOMATIC1111 WebUI Installer for Project Trinity.

This module provides cross-platform installation and configuration for the AUTOMATIC1111
Stable Diffusion WebUI, including extensions and configuration files.

Author: Trinity Project Team
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
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Setup project paths with safe __file__ handling
try:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
except NameError:
    # Fallback when __file__ is not available (e.g., when using exec())
    PROJECT_ROOT = Path.cwd()
    logger.warning("__file__ not available, using current working directory as PROJECT_ROOT")

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
UI_NAME = 'A1111'
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

# Initialize paths and configuration
ENVIRONMENT_PATHS = get_environment_paths()
HOME_PATH = ENVIRONMENT_PATHS.get('home_path', Path.cwd())
VENV_PATH = ENVIRONMENT_PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = ENVIRONMENT_PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI_PATH = HOME_PATH / UI_NAME
EXTENSIONS_PATH = WEBUI_PATH / 'extensions'

# Configuration values with safe fallbacks
ENV_NAME = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.env_name', 'Colab')
FORK_REPO = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.fork', 'remphanostar/TrinityUI')
BRANCH = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.branch', 'main')

# Change to home directory if it exists
if HOME_PATH.exists():
    os.chdir(HOME_PATH)

# ==================== WEBUI OPERATIONS ====================

async def download_file(url: str, directory: Path, filename: str) -> bool:
    """
    Cross-platform file download using urllib.
    
    Args:
        url: The URL to download from
        directory: Target directory for the file
        filename: Name for the downloaded file
        
    Returns:
        True if download successful, False otherwise
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    
    # Remove existing file if present
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as e:
            logger.warning(f"Could not remove existing file {file_path}: {e}")
    
    try:
        # Create SSL context for compatibility
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"Downloading {url} to {file_path}")
        urllib.request.urlretrieve(url, file_path)
        logger.info(f"Successfully downloaded {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False

async def download_files_batch(file_list: List[str]) -> List[bool]:
    """
    Download multiple files concurrently.
    
    Args:
        file_list: List of comma-separated strings in format: "url,directory,filename"
        
    Returns:
        List of boolean results for each download
    """
    tasks = []
    for file_info in file_list:
        parts = [part.strip() for part in file_info.split(',')]
        if len(parts) < 1:
            logger.warning(f"Invalid file info format: {file_info}")
            continue
            
        url = parts[0]
        directory = Path(parts[1]) if len(parts) > 1 else WEBUI_PATH
        filename = parts[2] if len(parts) > 2 else Path(url).name
        
        tasks.append(download_file(url, directory, filename))
    
    if not tasks:
        return []
        
    return await asyncio.gather(*tasks, return_exceptions=True)

async def download_configuration() -> bool:
    """
    Download configuration files and extensions for A1111.
    
    Returns:
        True if all downloads successful, False otherwise
    """
    logger.info("Downloading configuration files and extensions")
    
    # Configuration files to download
    url_config_base = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    config_files = [
        f"{url_config_base}/styles.csv,{WEBUI_PATH}",
        f"{url_config_base}/user.css,{WEBUI_PATH}",
        f"{url_config_base}/card-no-preview.png,{WEBUI_PATH}/html",
        f"{url_config_base}/notification.mp3,{WEBUI_PATH}",
        f"{url_config_base}/gradio-tunneling.py,{VENV_PATH}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    
    # Download configuration files
    config_results = await download_files_batch(config_files)
    config_success = all(result is True for result in config_results if not isinstance(result, Exception))
    
    # Clone extensions
    extensions_success = await clone_extensions()
    
    return config_success and extensions_success

async def clone_extensions() -> bool:
    """
    Clone A1111 extensions from GitHub repositories.
    
    Returns:
        True if all extensions cloned successfully, False otherwise
    """
    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',
        'https://github.com/gutris1/sd-image-viewer Image-Viewer',
        'https://github.com/gutris1/sd-image-info Image-Info',
        'https://github.com/gutris1/sd-hub SD-Hub',
        'https://github.com/Bing-su/adetailer',
        'https://github.com/Haoming02/sd-forge-couple SD-Couple',
        'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    ]
    
    # Add Kaggle-specific extension
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')

    EXTENSIONS_PATH.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    
    try:
        os.chdir(EXTENSIONS_PATH)
        logger.info(f"Cloning extensions into {EXTENSIONS_PATH}")
        
        processes = []
        for extension_command in extensions_list:
            # Parse repository name
            parts = extension_command.split()
            repo_url = parts[0]
            repo_name_git = repo_url.split('/')[-1]
            if repo_name_git.endswith('.git'):
                repo_name_git = repo_name_git[:-4]
            repo_name = parts[1] if len(parts) > 1 else repo_name_git
            
            extension_path = EXTENSIONS_PATH / repo_name
            if extension_path.exists():
                logger.info(f"Extension '{repo_name}' already exists. Skipping clone.")
                continue

            # Create subprocess for git clone
            try:
                logger.info(f"Cloning '{repo_name}' from {repo_url}")
                process = await asyncio.create_subprocess_shell(
                    f"git clone --depth 1 {repo_url} {repo_name}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                processes.append((process, repo_name))
            except Exception as e:
                logger.error(f"Failed to start git clone for {repo_name}: {e}")

        # Wait for all clones to complete
        results = await asyncio.gather(
            *[process.communicate() for process, _ in processes],
            return_exceptions=True
        )

        # Check results
        success = True
        for i, (stdout, stderr) in enumerate(results):
            if isinstance(results[i], Exception):
                logger.error(f"Exception during git clone: {results[i]}")
                success = False
                continue
                
            process, repo_name = processes[i]
            if process.returncode != 0:
                stderr_str = stderr.decode().strip() if stderr else 'No stderr output'
                logger.error(f"Failed to clone extension '{repo_name}': {stderr_str}")
                if stdout and stdout.decode().strip():
                    logger.debug(f"Git stdout for {repo_name}: {stdout.decode().strip()}")
                success = False
            else:
                logger.info(f"Successfully cloned extension '{repo_name}'")
                
        return success
        
    except Exception as e:
        logger.error(f"Error during extension cloning: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def install_webui() -> bool:
    """
    Download and extract the A1111 WebUI from HuggingFace.
    
    Returns:
        True if installation successful, False otherwise
    """
    zip_path = HOME_PATH / f"{UI_NAME}.zip"
    logger.info(f"Downloading WebUI from {WEBUI_REPO_URL}")
    
    # Download the WebUI zip file
    download_successful = download_url_to_path(
        url=WEBUI_REPO_URL, 
        target_full_path=str(zip_path), 
        log=True
    )
    
    if not download_successful:
        logger.error(f"Download failed for {WEBUI_REPO_URL}. Cannot proceed with A1111 setup.")
        return False

    logger.info(f"Extracting {zip_path} to {WEBUI_PATH}")
    
    # Extract the zip file using Python's zipfile module
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(WEBUI_PATH)
        logger.info(f"Successfully extracted {zip_path} to {WEBUI_PATH}")
    except Exception as e:
        logger.error(f"Error during zip extraction: {e}")
        return False

    # Clean up the zip file
    logger.info(f"Removing {zip_path}")
    try:
        zip_path.unlink()
        logger.info(f"Successfully removed {zip_path}")
    except Exception as e:
        logger.warning(f"Could not remove zip file {zip_path}: {e}")
    
    return True

# ======================== MAIN CODE =======================

async def main() -> bool:
    """
    Main installation function for A1111 WebUI.
    
    Returns:
        True if installation successful, False otherwise
    """
    logger.info(f"AnxLight {UI_NAME} UI Installer Script")
    
    try:
        # Step 1: Install WebUI
        logger.info("Step 1: Installing A1111 WebUI...")
        webui_success = install_webui()
        if not webui_success:
            logger.error("WebUI installation failed")
            return False
        
        # Step 2: Download configuration and extensions
        logger.info("Step 2: Downloading configuration and extensions...")
        config_success = await download_configuration()
        if not config_success:
            logger.warning("Some configuration downloads failed, but continuing...")
        
        logger.info("A1111 installation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        return False

def run_installer() -> int:
    """
    Run the A1111 installer.
    
    Returns:
        0 if successful, 1 if failed
    """
    try:
        success = asyncio.run(main())
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Installation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

if __name__ == '__main__':
    exit_code = run_installer()
    sys.exit(exit_code)