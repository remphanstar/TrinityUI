"""
TrinityUI Installation Manager
Handles WebUI dependency installation and asset downloads with progress tracking
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
import requests

class InstallationProgressTracker:
    def __init__(self, notebook_callback: Optional[Callable] = None, gradio_callback: Optional[Callable] = None):
        self.notebook_callback = notebook_callback
        self.gradio_callback = gradio_callback
        self.dependency_log = []
        self.asset_progress = []
        self.installation_start_time = None
        self.current_phase = "initializing"
        
    def log(self, message: str, level: str = "INFO", phase: str = None):
        """Log message to both notebook and Gradio outputs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        if phase:
            self.current_phase = phase
            
        self.dependency_log.append(log_entry)
        
        # Send to notebook output
        if self.notebook_callback:
            self.notebook_callback(f"{log_entry}\n")
            
        # Send to Gradio output
        if self.gradio_callback:
            formatted_log = self.format_log_for_display()
            self.gradio_callback("dependency_progress", formatted_log)
    
    def format_log_for_display(self) -> str:
        """Format dependency log for HTML display"""
        formatted_lines = []
        for line in self.dependency_log[-50:]:  # Keep last 50 lines
            if "[ERROR]" in line:
                formatted_lines.append(f'<div class="log-line log-error">{line}</div>')
            elif "[WARNING]" in line:
                formatted_lines.append(f'<div class="log-line log-warning">{line}</div>')
            elif "[SUCCESS]" in line:
                formatted_lines.append(f'<div class="log-line log-success">{line}</div>')
            else:
                formatted_lines.append(f'<div class="log-line log-info">{line}</div>')
        return ''.join(formatted_lines)
    
    def update_asset_progress(self, asset_name: str, status: str, error: str = None):
        """Update asset download progress"""
        # Update existing asset or add new one
        asset_found = False
        for asset in self.asset_progress:
            if asset['name'] == asset_name:
                asset['status'] = status
                if error:
                    asset['error'] = error
                asset_found = True
                break
        
        if not asset_found:
            asset_entry = {'name': asset_name, 'status': status}
            if error:
                asset_entry['error'] = error
            self.asset_progress.append(asset_entry)
        
        # Send to Gradio output
        if self.gradio_callback:
            self.gradio_callback("asset_progress", self.asset_progress)
    
    def start_installation(self):
        """Mark installation start"""
        self.installation_start_time = time.time()
        self.log("Starting WebUI installation process", "INFO", "starting")
    
    def complete_installation(self, success: bool = True):
        """Mark installation completion"""
        duration = time.time() - self.installation_start_time if self.installation_start_time else 0
        if success:
            self.log(f"Installation completed successfully in {duration:.1f} seconds", "SUCCESS", "completed")
        else:
            self.log(f"Installation completed with errors after {duration:.1f} seconds", "ERROR", "completed")
        
        if self.gradio_callback:
            self.gradio_callback("completion", success)

class TrinityInstallationManager:
    def __init__(self, project_root: Path, tracker: InstallationProgressTracker):
        self.project_root = project_root
        self.tracker = tracker
        self.webui_root = Path('/content')
        
    def install_webui_dependencies(self, webui_choice: str) -> bool:
        """Install dependencies for the selected WebUI"""
        self.tracker.log(f"Installing dependencies for {webui_choice}", "INFO", "dependencies")
        
        webui_path = self.webui_root / webui_choice
        venv_path = webui_path / 'venv'
        venv_python = venv_path / 'bin' / 'python'
        venv_pip = venv_path / 'bin' / 'pip'
        
        if not webui_path.exists():
            self.tracker.log(f"WebUI directory not found: {webui_path}", "ERROR")
            return False
            
        if not venv_path.exists():
            self.tracker.log(f"Virtual environment not found: {venv_path}", "ERROR")
            return False
        
        # Check if dependencies already installed
        try:
            result = subprocess.run(
                [str(venv_python), '-c', 'import torch; print("PyTorch version:", torch.__version__)'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.tracker.log(f"Dependencies already installed for {webui_choice}", "SUCCESS")
                self.tracker.log(f"PyTorch status: {result.stdout.strip()}", "INFO")
                return True
        except Exception:
            pass
        
        # Install requirements
        requirements_files = [
            webui_path / 'requirements_versions.txt',
            webui_path / 'requirements.txt'
        ]
        
        requirements_file = None
        for req_file in requirements_files:
            if req_file.exists():
                requirements_file = req_file
                break
        
        if not requirements_file:
            self.tracker.log(f"No requirements file found for {webui_choice}", "ERROR")
            return False
        
        self.tracker.log(f"Installing from {requirements_file.name}", "INFO")
        
        try:
            # Upgrade pip first
            self.tracker.log("Upgrading pip in virtual environment", "INFO")
            pip_upgrade_cmd = [str(venv_pip), 'install', '--upgrade', 'pip', 'setuptools', 'wheel']
            
            process = subprocess.Popen(
                pip_upgrade_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=webui_path
            )
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.tracker.log(f"PIP: {line.strip()}", "INFO")
            
            process.wait()
            
            # Install requirements
            self.tracker.log(f"Installing requirements from {requirements_file.name}", "INFO")
            install_cmd = [
                str(venv_pip), 'install', '-r', str(requirements_file),
                '--cache-dir', '/tmp/pip-cache',
                '--trusted-host', 'pypi.org',
                '--trusted-host', 'pypi.python.org', 
                '--trusted-host', 'files.pythonhosted.org',
                '--progress-bar', 'on'
            ]
            
            process = subprocess.Popen(
                install_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=webui_path
            )
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.tracker.log(f"INSTALL: {line.strip()}", "INFO")
            
            return_code = process.wait()
            
            if return_code == 0:
                self.tracker.log(f"Successfully installed {webui_choice} dependencies", "SUCCESS")
                return True
            else:
                self.tracker.log(f"Dependency installation failed with exit code {return_code}", "ERROR")
                return False
                
        except Exception as e:
            self.tracker.log(f"Exception during dependency installation: {e}", "ERROR")
            return False
    
    def load_model_data(self, is_xl: bool = False) -> tuple:
        """Load model data from repository files"""
        try:
            if is_xl:
                data_file = self.project_root / 'scripts' / '_xl-models-data.py'
            else:
                data_file = self.project_root / 'scripts' / '_models-data.py'
            
            if not data_file.exists():
                self.tracker.log(f"Model data file not found: {data_file}", "ERROR")
                return {}, {}, {}, {}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            namespace = {}
            exec(content, namespace)
            
            model_list = namespace.get('model_list', {})
            vae_list = namespace.get('vae_list', {})
            controlnet_list = namespace.get('controlnet_list', {})
            lora_list = namespace.get('lora_list', {})
            
            self.tracker.log(f"Loaded data: {len(model_list)} models, {len(vae_list)} VAEs, {len(controlnet_list)} ControlNets, {len(lora_list)} LoRAs", "SUCCESS")
            
            return model_list, vae_list, controlnet_list, lora_list
            
        except Exception as e:
            self.tracker.log(f"Error loading model data: {e}", "ERROR")
            return {}, {}, {}, {}
    
    def get_webui_directories(self, webui_choice: str) -> Dict[str, Path]:
        """Get correct directory structure for different WebUIs"""
        webui_path = self.webui_root / webui_choice
        
        if webui_choice == 'ComfyUI':
            return {
                'models': webui_path / 'models' / 'checkpoints',
                'vae': webui_path / 'models' / 'vae',
                'controlnet': webui_path / 'models' / 'controlnet',
                'lora': webui_path / 'models' / 'loras'
            }
        else:  # A1111, Forge, etc.
            return {
                'models': webui_path / 'models' / 'Stable-diffusion',
                'vae': webui_path / 'models' / 'VAE',
                'controlnet': webui_path / 'models' / 'ControlNet',
                'lora': webui_path / 'models' / 'Lora'
            }
    
    def download_single_asset(self, url: str, output_path: Path, filename: str) -> tuple:
        """Download a single asset with aria2c acceleration"""
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'aria2c',
                '--max-connection-per-server=16',
                '--split=16',
                '--min-split-size=1M',
                '--continue=true',
                '--retry-wait=3',
                '--max-tries=5',
                '--dir', str(output_path),
                '--out', filename,
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            file_path = output_path / filename
            if result.returncode == 0 and file_path.exists() and file_path.stat().st_size > 0:
                return True, f"Downloaded {filename} successfully"
            else:
                return False, f"Download failed: {result.stderr[:200] if result.stderr else 'Unknown error'}"
                
        except subprocess.TimeoutExpired:
            return False, f"Download timed out for {filename}"
        except Exception as e:
            return False, f"Download error for {filename}: {e}"
    
    def download_selected_assets(self, config: Dict[str, Any]) -> bool:
        """Download only the selected assets"""
        webui_choice = config.get('webui_choice', 'A1111')
        is_xl = config.get('sd_version') == 'SDXL'
        
        selected_models = config.get('selected_models', [])
        selected_vaes = config.get('selected_vaes', [])
        selected_controlnets = config.get('selected_controlnets', [])
        selected_loras = config.get('selected_loras', [])
        
        self.tracker.log(f"Starting asset downloads for {webui_choice}", "INFO", "assets")
        self.tracker.log(f"Selected: {len(selected_models)} models, {len(selected_vaes)} VAEs, {len(selected_controlnets)} ControlNets, {len(selected_loras)} LoRAs", "INFO")
        
        if not any([selected_models, selected_vaes, selected_controlnets, selected_loras]):
            self.tracker.log("No assets selected for download", "SUCCESS")
            return True
        
        # Load model data
        model_list, vae_list, controlnet_list, lora_list = self.load_model_data(is_xl)
        
        if not any([model_list, vae_list, controlnet_list, lora_list]):
            self.tracker.log("Failed to load model data files", "ERROR")
            return False
        
        # Get directory structure
        directories = self.get_webui_directories(webui_choice)
        
        download_tasks = []
        
        # Prepare download tasks for selected items only
        asset_types = [
            (selected_models, model_list, directories['models'], 'Model'),
            (selected_vaes, vae_list, directories['vae'], 'VAE'),
            (selected_controlnets, controlnet_list, directories['controlnet'], 'ControlNet'),
            (selected_loras, lora_list, directories['lora'], 'LoRA')
        ]
        
        for selected_items, data_dict, target_dir, asset_type in asset_types:
            for item_name in selected_items:
                if item_name in data_dict:
                    for item in data_dict[item_name]:
                        url = item.get('url', '')
                        filename = item.get('name', url.split('/')[-1])
                        if url and filename:
                            download_tasks.append({
                                'url': url,
                                'path': target_dir,
                                'filename': filename,
                                'type': asset_type,
                                'selection': item_name
                            })
        
        if not download_tasks:
            self.tracker.log("No valid download URLs found for selections", "ERROR")
            return False
        
        self.tracker.log(f"Starting download of {len(download_tasks)} files", "INFO")
        
        # Initialize progress tracking for all assets
        for task in download_tasks:
            self.tracker.update_asset_progress(task['filename'], 'pending')
        
        # Download assets
        success_count = 0
        total_count = len(download_tasks)
        
        for i, task in enumerate(download_tasks, 1):
            asset_name = task['filename']
            self.tracker.log(f"[{i}/{total_count}] Downloading {task['type']} from '{task['selection']}': {asset_name}", "INFO")
            self.tracker.update_asset_progress(asset_name, 'downloading')
            
            # Check if file already exists
            file_path = task['path'] / task['filename']
            if file_path.exists() and file_path.stat().st_size > 1024*1024:  # > 1MB
                self.tracker.log(f"Already exists: {asset_name}", "SUCCESS")
                self.tracker.update_asset_progress(asset_name, 'success')
                success_count += 1
                continue
            
            success, message = self.download_single_asset(task['url'], task['path'], task['filename'])
            
            if success:
                success_count += 1
                self.tracker.log(f"✅ {message}", "SUCCESS")
                self.tracker.update_asset_progress(asset_name, 'success')
            else:
                self.tracker.log(f"❌ {message}", "ERROR")
                self.tracker.update_asset_progress(asset_name, 'error', message)
        
        self.tracker.log(f"Download Summary: {success_count}/{total_count} assets downloaded successfully", "SUCCESS")
        return success_count > 0

def run_installation(config: Dict[str, Any], tracker: InstallationProgressTracker) -> bool:
    """Run complete installation process"""
    project_root = Path('/content/TrinityUI')
    manager = TrinityInstallationManager(project_root, tracker)
    
    tracker.start_installation()
    
    try:
        webui_choice = config.get('webui_choice', 'A1111')
        
        # Phase 1: Install dependencies
        tracker.log("Phase 1: Installing WebUI dependencies", "INFO", "dependencies")
        deps_success = manager.install_webui_dependencies(webui_choice)
        
        if not deps_success:
            tracker.log("Dependency installation failed", "ERROR")
            tracker.complete_installation(False)
            return False
        
        # Phase 2: Download assets
        tracker.log("Phase 2: Downloading selected assets", "INFO", "assets")
        assets_success = manager.download_selected_assets(config)
        
        if not assets_success:
            tracker.log("Asset download failed", "ERROR")
            tracker.complete_installation(False)
            return False
        
        tracker.complete_installation(True)
        return True
        
    except Exception as e:
        tracker.log(f"Installation failed with exception: {e}", "ERROR")
        tracker.complete_installation(False)
        return False
