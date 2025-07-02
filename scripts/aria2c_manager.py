"""
TrinityUI Aria2c Download Manager
Handles high-speed downloads with aria2c acceleration
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Aria2cManager:
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('/tmp/trinity_cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.config_file = self.setup_aria2c_config()
    
    def setup_aria2c_config(self) -> str:
        """Setup aria2c configuration for optimal performance"""
        config = {
            'max-connection-per-server': '16',
            'max-concurrent-downloads': '16',
            'split': '16',
            'min-split-size': '1M',
            'continue': 'true',
            'auto-file-renaming': 'false',
            'allow-overwrite': 'true',
            'retry-wait': '3',
            'max-tries': '5',
            'file-allocation': 'none',
            'check-integrity': 'true'
        }
        
        config_file = Path('/tmp/aria2c_trinity.conf')
        with open(config_file, 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        return str(config_file)
    
    def download_file(self, url: str, output_path: Path, filename: str) -> Tuple[bool, str]:
        """Download a single file with aria2c"""
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'aria2c',
                f'--conf-path={self.config_file}',
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
    
    def batch_download_pytorch_wheels(self) -> bool:
        """Pre-download PyTorch wheels for faster installation"""
        wheels = {
            'torch-2.1.2+cu121': 'https://download.pytorch.org/whl/cu121/torch-2.1.2%2Bcu121-cp310-cp310-linux_x86_64.whl',
            'torchvision-0.16.2+cu121': 'https://download.pytorch.org/whl/cu121/torchvision-0.16.2%2Bcu121-cp310-cp310-linux_x86_64.whl',
            'torchaudio-2.1.2+cu121': 'https://download.pytorch.org/whl/cu121/torchaudio-2.1.2%2Bcu121-cp310-cp310-linux_x86_64.whl',
            'torch-2.3.1+cu121': 'https://download.pytorch.org/whl/cu121/torch-2.3.1%2Bcu121-cp311-cp311-linux_x86_64.whl',
            'torchvision-0.18.1+cu121': 'https://download.pytorch.org/whl/cu121/torchvision-0.18.1%2Bcu121-cp311-cp311-linux_x86_64.whl'
        }
        
        pytorch_cache = self.cache_dir / 'pytorch'
        pytorch_cache.mkdir(exist_ok=True)
        
        # Create download list for aria2c
        download_file = pytorch_cache / 'pytorch_downloads.txt'
        with open(download_file, 'w') as f:
            for name, url in wheels.items():
                f.write(f"{url}\n")
                f.write(f" dir={pytorch_cache}\n")
                f.write(f" out={name}.whl\n\n")
        
        # Download with aria2c
        cmd = f"aria2c --conf-path={self.config_file} --input-file={download_file}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return result.returncode == 0
