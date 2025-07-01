"""
ReForge WebUI Installer for Project Trinity.

This module provides cross-platform installation and configuration for the ReForge WebUI.
Note: Panchovix/stable-diffusion-webui-reForge development has reportedly stopped.

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
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Iterator
from urllib.parse import urlparse

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
UI_NAME = 'ReForge'
REFORGE_GIT_REPO_URL = "https://github.com/Panchovix/stable-diffusion-webui-reForge.git"

@dataclass(frozen=True)
class ReForgeConfig:
    """Configuration container for ReForge installation."""
    ui_name: str = UI_NAME
    repo_url: str = REFORGE_GIT_REPO_URL
    default_env_name: str = 'Colab'
    default_fork_repo: str = 'remphanostar/TrinityUI'
    default_branch: str = 'main'
    python_version: str = '3.10'  # For gradio-tunneling path

class ReForgeError(Exception):
    """Base exception for ReForge installation errors."""
    pass

class ConfigurationError(ReForgeError):
    """Raised when configuration cannot be read or is invalid."""
    pass

class DownloadError(ReForgeError):
    """Raised when file download fails."""
    pass

class GitOperationError(ReForgeError):
    """Raised when git operations fail."""
    pass

# Environment paths helper functions
def get_environment_paths() -> dict[str, Path]:
    """Get environment paths from environment variables."""
    paths = {}
    for key, value in os.environ.items():
        if key.endswith('_path'):
            try:
                paths[key] = Path(value)
            except (TypeError, ValueError) as e:
                logger.warning(f"Invalid path in environment variable {key}='{value}': {e}")
    return paths

def get_configuration_value(settings_path: Path, key: str, default: str) -> str:
    """
    Safely read configuration value with fallback.
    
    Args:
        settings_path: Path to settings file
        key: Configuration key to read
        default: Default value if key not found or error occurs
        
    Returns:
        Configuration value or default
        
    Raises:
        ConfigurationError: If settings file exists but is malformed
    """
    if not settings_path.exists():
        logger.debug(f"Settings file {settings_path} not found, using default for {key}: {default}")
        return default
    
    try:
        return json_utils.read(settings_path, key)
    except (KeyError, ValueError) as e:
        logger.warning(f"Config key '{key}' not found or invalid: {e}. Using default: {default}")
        return default
    except Exception as e:
        raise ConfigurationError(f"Failed to read configuration from {settings_path}: {e}") from e

@contextmanager
def change_directory(target_path: Path) -> Iterator[Path]:
    """
    Context manager for safely changing directories.
    
    Args:
        target_path: Directory to change to
        
    Yields:
        The target path
        
    Raises:
        OSError: If directory change fails
    """
    original_cwd = Path.cwd()
    try:
        os.chdir(target_path)
        logger.debug(f"Changed directory to: {target_path}")
        yield target_path
    except OSError as e:
        raise OSError(f"Failed to change directory to {target_path}: {e}") from e
    finally:
        try:
            os.chdir(original_cwd)
            logger.debug(f"Restored directory to: {original_cwd}")
        except OSError as e:
            logger.error(f"Failed to restore directory to {original_cwd}: {e}")

def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

# Initialize configuration
config = ReForgeConfig()
ENVIRONMENT_PATHS = get_environment_paths()
HOME_PATH = ENVIRONMENT_PATHS.get('home_path', Path.cwd())
VENV_PATH = ENVIRONMENT_PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = ENVIRONMENT_PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI_PATH = HOME_PATH / config.ui_name
EXTENSIONS_PATH = WEBUI_PATH / 'extensions'

# Configuration values with safe fallbacks
ENV_NAME = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.env_name', config.default_env_name)
FORK_REPO = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.fork', config.default_fork_repo)
BRANCH = get_configuration_value(SETTINGS_PATH, 'ENVIRONMENT.branch', config.default_branch)

# Initialize working directory
if HOME_PATH.exists() and HOME_PATH.is_dir():
    try:
        os.chdir(HOME_PATH)
        logger.debug(f"Set working directory to: {HOME_PATH}")
    except OSError as e:
        logger.warning(f"Failed to change to home directory {HOME_PATH}: {e}")
else:
    logger.warning(f"Home path {HOME_PATH} does not exist or is not a directory")

# ==================== WEBUI OPERATIONS ====================

async def download_file(url: str, directory: Path, filename: str) -> bool:
    """
    Cross-platform file download using urllib with comprehensive error handling.
    
    Args:
        url: The URL to download from
        directory: Target directory for the file
        filename: Name for the downloaded file
        
    Returns:
        True if download successful, False otherwise
        
    Raises:
        DownloadError: If download fails due to network or file system issues
    """
    if not validate_url(url):
        raise DownloadError(f"Invalid URL format: {url}")
    
    directory = Path(directory)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise DownloadError(f"Failed to create directory {directory}: {e}") from e
    
    file_path = directory / filename
    
    # Remove existing file if present
    if file_path.exists():
        try:
            file_path.unlink()
            logger.debug(f"Removed existing file: {file_path}")
        except OSError as e:
            logger.warning(f"Could not remove existing file {file_path}: {e}")
    
    try:
        # Create SSL context for compatibility
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"Downloading {url} to {file_path}")
        
        # Use urllib with SSL context
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, context=ssl_context) as response:
            with open(file_path, 'wb') as f:
                f.write(response.read())
        
        logger.info(f"Successfully downloaded {filename}")
        return True
        
    except urllib.error.URLError as e:
        raise DownloadError(f"Network error downloading {url}: {e}") from e
    except urllib.error.HTTPError as e:
        raise DownloadError(f"HTTP error {e.code} downloading {url}: {e}") from e
    except OSError as e:
        raise DownloadError(f"File system error saving {filename}: {e}") from e
    except Exception as e:
        raise DownloadError(f"Unexpected error downloading {url}: {e}") from e

async def download_files_batch(file_list: List[str]) -> List[bool]:
    """
    Download multiple files concurrently with robust error handling.
    
    Args:
        file_list: List of comma-separated strings in format: "url,directory,filename"
        
    Returns:
        List of boolean results for each download
        
    Raises:
        ValueError: If file_list format is invalid
    """
    if not file_list:
        logger.warning("Empty file list provided to download_files_batch")
        return []
    
    tasks = []
    for file_info in file_list:
        try:
            parts = [part.strip() for part in file_info.split(',')]
            if len(parts) < 1:
                logger.warning(f"Invalid file info format: {file_info}")
                continue
                
            url = parts[0]
            directory = Path(parts[1]) if len(parts) > 1 else WEBUI_PATH
            filename = parts[2] if len(parts) > 2 else Path(url).name
            
            if not filename:
                filename = f"downloaded_file_{len(tasks)}"
                logger.warning(f"No filename detected for {url}, using: {filename}")
            
            tasks.append(download_file(url, directory, filename))
            
        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing file info '{file_info}': {e}")
            continue
    
    if not tasks:
        logger.warning("No valid download tasks created from file list")
        return []
        
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and log failures
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Download task {i} failed with exception: {result}")
            elif result is True:
                success_count += 1
            else:
                logger.error(f"Download task {i} failed")
        
        logger.info(f"Download batch completed: {success_count}/{len(results)} successful")
        return [result if isinstance(result, bool) else False for result in results]
        
    except Exception as e:
        logger.error(f"Unexpected error in download batch: {e}")
        return [False] * len(tasks)

async def download_configuration() -> bool:
    """
    Download configuration files and extensions for ReForge.
    
    Returns:
        True if all downloads successful, False otherwise
        
    Raises:
        ConfigurationError: If configuration cannot be determined
        DownloadError: If critical downloads fail
    """
    logger.info("Downloading configuration files and extensions (review for ReForge compatibility)")
    
    try:
        # Configuration files to download
        url_config_base = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
        
        # Validate base URL
        if not validate_url(url_config_base):
            raise ConfigurationError(f"Invalid configuration base URL: {url_config_base}")
        
        config_files = [
            f"{url_config_base}/styles.csv,{WEBUI_PATH}",
            f"{url_config_base}/user.css,{WEBUI_PATH}",
            f"{url_config_base}/card-no-preview.png,{WEBUI_PATH}/html",
            f"{url_config_base}/notification.mp3,{WEBUI_PATH}",
            f"{url_config_base}/gradio-tunneling.py,{VENV_PATH}/lib/python{config.python_version}/site-packages/gradio_tunneling,main.py"
        ]
        
        # Download configuration files
        config_results = await download_files_batch(config_files)
        config_success = sum(config_results) > 0  # At least some files should succeed
        
        if not config_success:
            logger.warning("No configuration files downloaded successfully")
        
        # Clone extensions
        extensions_success = await clone_extensions()
        
        overall_success = config_success and extensions_success
        if overall_success:
            logger.info("Configuration download completed successfully")
        else:
            logger.warning("Some configuration downloads failed")
            
        return overall_success
        
    except Exception as e:
        logger.error(f"Error during configuration download: {e}")
        return False

async def clone_extensions() -> bool:
    """
    Clone ReForge extensions from GitHub repositories with comprehensive error handling.
    
    Returns:
        True if all extensions cloned successfully, False otherwise
        
    Raises:
        GitOperationError: If critical git operations fail
    """
    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',
        'https://github.com/gutris1/sd-image-viewer Image-Viewer',
        'https://github.com/gutris1/sd-image-info Image-Info',
        'https://github.com/gutris1/sd-hub SD-Hub',
        'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    ]
    
    # Add environment-specific extensions
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')
        logger.info("Added Kaggle-specific extensions")

    try:
        EXTENSIONS_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cloning extensions into {EXTENSIONS_PATH} (review for ReForge compatibility)")
        
        with change_directory(EXTENSIONS_PATH):
            processes = []
            valid_extensions = []
            
            for extension_command in extensions_list:
                try:
                    # Parse repository name and URL
                    parts = extension_command.split()
                    repo_url = parts[0]
                    repo_name = parts[1] if len(parts) > 1 else repo_url.split('/')[-1].replace('.git', '')
                    
                    # Validate repository URL
                    if not validate_url(repo_url):
                        logger.warning(f"Invalid repository URL: {repo_url}")
                        continue
                    
                    extension_path = EXTENSIONS_PATH / repo_name
                    if extension_path.exists():
                        logger.info(f"Extension '{repo_name}' already exists. Skipping clone.")
                        continue

                    # Create subprocess for git clone
                    process = await asyncio.create_subprocess_shell(
                        f"git clone --depth 1 {repo_url} {repo_name}",
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE
                    )
                    processes.append((process, repo_name, repo_url))
                    valid_extensions.append(extension_command)
                    
                except Exception as e:
                    logger.error(f"Failed to start git clone for {extension_command}: {e}")
                    continue

            if not processes:
                logger.warning("No extension cloning processes started")
                return True  # No extensions to clone is not a failure

            # Wait for all clones to complete
            try:
                results = await asyncio.gather(
                    *[process.communicate() for process, _, _ in processes],
                    return_exceptions=True
                )
            except Exception as e:
                raise GitOperationError(f"Failed to complete extension cloning: {e}") from e

            # Check results and provide detailed feedback
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    _, repo_name, repo_url = processes[i]
                    logger.error(f"Exception during git clone of '{repo_name}': {result}")
                    continue
                    
                process, repo_name, repo_url = processes[i]
                stdout, stderr = result
                
                if process.returncode == 0:
                    logger.info(f"Successfully cloned extension '{repo_name}'")
                    success_count += 1
                else:
                    error_msg = stderr.decode() if stderr else 'No stderr output'
                    logger.error(f"Failed to clone extension '{repo_name}' from {repo_url}: {error_msg}")

            logger.info(f"Extension cloning completed: {success_count}/{len(processes)} successful")
            return success_count > 0  # At least one extension should succeed
            
    except OSError as e:
        raise GitOperationError(f"File system error during extension cloning: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during extension cloning: {e}")
        return False

def install_webui() -> bool:
    """
    Clone the ReForge WebUI repository with comprehensive error handling.
    
    Returns:
        True if installation successful, False otherwise
        
    Raises:
        GitOperationError: If git operations fail critically
    """
    logger.info(f"Installing WebUI from {config.repo_url} into {WEBUI_PATH}")
    
    # Validate repository URL
    if not validate_url(config.repo_url):
        raise GitOperationError(f"Invalid repository URL: {config.repo_url}")
    
    if WEBUI_PATH.exists():
        if not WEBUI_PATH.is_dir():
            raise GitOperationError(f"Path {WEBUI_PATH} exists but is not a directory")
        
        logger.info(f"Directory {WEBUI_PATH} already exists. Assuming ReForge is already cloned.")
        
        # Optionally verify it's a git repository
        git_dir = WEBUI_PATH / '.git'
        if git_dir.exists():
            logger.info("Existing installation appears to be a git repository")
            return True
        else:
            logger.warning("Existing installation is not a git repository")
            return True
    
    try:
        logger.info("Cloning ReForge repository...")
        
        # Clone the repository with specific error handling
        result = subprocess.run(
            ["git", "clone", config.repo_url, str(WEBUI_PATH)], 
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        logger.info("ReForge cloned successfully. Checking out main branch...")
        
        # Checkout main branch
        checkout_result = subprocess.run(
            ["git", "checkout", "main"], 
            cwd=str(WEBUI_PATH), 
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        logger.info("ReForge repository installation completed successfully")
        return True
        
    except subprocess.TimeoutExpired as e:
        raise GitOperationError(f"Git operation timed out: {e}") from e
    except subprocess.CalledProcessError as e:
        error_details = f"Return code: {e.returncode}"
        if e.stderr:
            error_details += f", stderr: {e.stderr.strip()}"
        if e.stdout:
            error_details += f", stdout: {e.stdout.strip()}"
        raise GitOperationError(f"Git operation failed: {error_details}") from e
    except FileNotFoundError:
        raise GitOperationError("Git command not found. Please ensure Git is installed and in PATH") from None
    except OSError as e:
        raise GitOperationError(f"System error during git operation: {e}") from e
    except Exception as e:
        raise GitOperationError(f"Unexpected error during WebUI installation: {e}") from e

# ======================== MAIN CODE =======================

async def main() -> bool:
    """
    Main installation function for ReForge WebUI with comprehensive error handling.
    
    Returns:
        True if installation successful, False otherwise
    """
    logger.info(f"AnxLight {config.ui_name} UI Installer Script")
    logger.warning(f"Note: {config.ui_name} development by Panchovix reportedly stopped")
    
    try:
        # Step 1: Install WebUI
        logger.info("Step 1: Installing ReForge WebUI...")
        webui_success = install_webui()
        if not webui_success:
            logger.error("WebUI installation failed")
            return False
        
        # Step 2: Download configuration and extensions
        logger.info("Step 2: Downloading configuration and extensions...")
        try:
            config_success = await download_configuration()
            if not config_success:
                logger.warning("Some configuration downloads failed, but continuing...")
                # Don't fail the entire installation for configuration issues
        except (ConfigurationError, DownloadError) as e:
            logger.error(f"Configuration download failed: {e}")
            logger.warning("Continuing installation without full configuration...")
        
        logger.info("ReForge installation completed successfully")
        return True
        
    except GitOperationError as e:
        logger.error(f"Git operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        return False

def run_installer() -> int:
    """
    Run the ReForge installer with proper exit code handling.
    
    Returns:
        0 if successful, 1 if failed
    """
    try:
        # Validate environment before starting
        if not HOME_PATH.exists():
            logger.error(f"Home path does not exist: {HOME_PATH}")
            return 1
        
        success = asyncio.run(main())
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Installation cancelled by user")
        return 1
    except (ConfigurationError, GitOperationError, DownloadError) as e:
        logger.error(f"Installation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug("Exception details:", exc_info=True)
        return 1

if __name__ == '__main__':
    exit_code = run_installer()
    sys.exit(exit_code)