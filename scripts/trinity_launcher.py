"""
TrinityUI Enhanced Launcher
Handles WebUI launching with proper Gradio URL detection
"""
import os
import sys
import json
import subprocess
import re
import time
from pathlib import Path
from typing import Optional, List

class TrinityLauncher:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_path = project_root / "trinity_config.json"
        
    def load_config(self) -> dict:
        """Load configuration from trinity_config.json"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            return {}
    
    def validate_environment(self, webui_choice: str) -> bool:
        """Validate that WebUI environment is ready"""
        webui_path = Path(f'/content/{webui_choice}')
        venv_python = webui_path / 'venv' / 'bin' / 'python'
        
        if not webui_path.exists():
            print(f"❌ WebUI path not found: {webui_path}")
            return False
            
        if not venv_python.exists():
            print(f"❌ Virtual environment not found: {venv_python}")
            return False
            
        return True
    
    def construct_launch_args(self, config: dict) -> List[str]:
        """Construct launch arguments ensuring --share is present"""
        custom_args = config.get('custom_args', '')
        webui_choice = config.get('webui_choice', 'A1111')
        
        args_list = custom_args.split() if custom_args else []
        
        # Force --share for Gradio
        if '--share' not in args_list:
            args_list.insert(0, '--share')
        
        # Add recommended args
        if '--xformers' not in args_list and webui_choice in ['A1111', 'Forge']:
            args_list.append('--xformers')
        
        if '--enable-insecure-extension-access' not in args_list:
            args_list.append('--enable-insecure-extension-access')
        
        return args_list
    
    def detect_gradio_url(self, line: str) -> Optional[str]:
        """Extract Gradio URL from output line"""
        patterns = [
            r'Running on public URL: (https?://[a-z0-9]+\.gradio\.live)',
            r'(https?://[a-z0-9]+\.gradio\.live)',
            r'(https?://[a-z0-9\-]+\.gradio\.app)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def launch_with_url_detection(self, config: dict, timeout: int = 300) -> bool:
        """Launch WebUI with enhanced Gradio URL detection"""
        webui_choice = config.get('webui_choice', 'A1111')
        
        if not self.validate_environment(webui_choice):
            return False
        
        webui_path = Path(f'/content/{webui_choice}')
        venv_python = webui_path / 'venv' / 'bin' / 'python'
        args_list = self.construct_launch_args(config)
        
        launch_cmd = [str(venv_python), 'launch.py'] + args_list
        
        print(f"🚀 Launching {webui_choice}")
        print(f"🔧 Arguments: {' '.join(args_list)}")
        print("📡 Waiting for Gradio public URL...")
        
        # Set environment
        env = os.environ.copy()
        env['MPLBACKEND'] = 'Agg'
        env['PYTHONUNBUFFERED'] = '1'
        
        try:
            process = subprocess.Popen(
                launch_cmd,
                cwd=webui_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            start_time = time.time()
            url_found = False
            
            while time.time() - start_time < timeout:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        print("❌ WebUI process ended unexpectedly")
                        break
                    time.sleep(0.1)
                    continue
                
                # Print important messages
                if any(keyword in line.lower() for keyword in [
                    'loading', 'model loaded', 'startup time', 'running on',
                    'local url', 'public url', 'gradio', 'error', 'traceback'
                ]):
                    print(f"   {line.strip()}")
                
                # Check for Gradio URL
                gradio_url = self.detect_gradio_url(line)
                if gradio_url:
                    print("\n" + "="*80)
                    print(f"🌐 GRADIO URL DETECTED: {gradio_url}")
                    print("="*80)
                    print(f"🎉 WebUI is ready! Access it at: {gradio_url}")
                    url_found = True
                    break
            
            if not url_found:
                print(f"❌ No Gradio URL found within {timeout} seconds")
                process.terminate()
                return False
            
            # Keep process running
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n✅ WebUI shutdown requested by user")
                process.terminate()
            
            return True
            
        except Exception as e:
            print(f"❌ Launch failed: {e}")
            return False
