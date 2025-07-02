"""
TrinityUI Enhanced Launcher with Repository-Based Styling
Version: 2.1.0 - Repository-based HTML/CSS/JS with auto-scroll
"""
import os
import sys
import json
import subprocess
import re
import time
import requests
from pathlib import Path
from typing import Optional, List
from IPython.display import HTML, display, clear_output
from datetime import datetime

class TrinityLauncher:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_path = project_root / "trinity_config.json"
        self.output_lines = []
        self.max_output_lines = 500
        self.html_loaded = False
        
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
    
    def load_html_from_repo(self) -> str:
        """Load HTML template from repository"""
        try:
            # Try local file first
            html_file = self.project_root / 'HTML' / 'trinity-launch-output.html'
            if html_file.exists():
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                print("🎨 Loaded Trinity styling from local repository")
                return content
            
            # Fallback to GitHub
            base_url = "https://raw.githubusercontent.com/remphanstar/TrinityUI/main/HTML"
            response = requests.get(f"{base_url}/trinity-launch-output.html", timeout=10)
            if response.status_code == 200:
                print("🎨 Loaded Trinity styling from GitHub repository")
                return response.text
            else:
                print(f"⚠️ Failed to load styling from GitHub: {response.status_code}")
                return self.get_fallback_html()
                
        except Exception as e:
            print(f"⚠️ Error loading Trinity styling: {e}")
            return self.get_fallback_html()
    
    def get_fallback_html(self) -> str:
        """Fallback HTML if repository files aren't available"""
        return """
        <style>
        .trinity-output-container {
            background: linear-gradient(135deg, #D2B48C 0%, #DEB887 50%, #F5DEB3 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            border: 3px solid #8B4513;
        }
        .trinity-output-content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        .output-line.success { color: #27AE60; font-weight: bold; }
        .output-line.error { color: #E74C3C; font-weight: bold; }
        .output-line.warning { color: #E67E22; }
        .output-line.info { color: #2C3E50; }
        </style>
        <div class="trinity-output-container">
            <div class="trinity-output-content" id="trinity-output-content">
                <div class="output-line info">Fallback styling loaded</div>
            </div>
        </div>
        <script>
        window.addOutputLine = function(line, type) {
            const container = document.getElementById('trinity-output-content');
            if (container) {
                const div = document.createElement('div');
                div.className = 'output-line ' + type;
                div.textContent = line;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }
        };
        window.showGradioLink = function(url) { console.log('Gradio URL:', url); };
        window.trinityOutputReady = true;
        </script>
        """
    
    def create_styled_output_container(self):
        """Create styled HTML container using repository files"""
        html_content = self.load_html_from_repo()
        display(HTML(html_content))
        self.html_loaded = True
        
        # Wait for initialization
        time.sleep(0.5)
    
    def add_output_line(self, line: str, line_type: str = "info"):
        """Add a line to the output with auto-scroll"""
        if not self.html_loaded:
            print(line)  # Fallback to regular print
            return
            
        clean_line = line.replace('\n', '').replace('\r', '').strip()
        if not clean_line:
            return
        
        # Escape quotes for JavaScript
        clean_line = clean_line.replace("'", "\\'").replace('"', '\\"')
        
        # Add to internal buffer
        self.output_lines.append(clean_line)
        if len(self.output_lines) > self.max_output_lines:
            self.output_lines.pop(0)
        
        # Add to display with auto-scroll
        display(HTML(f"""
        <script>
        if (window.trinityOutputReady && window.addOutputLine) {{
            window.addOutputLine('{clean_line}', '{line_type}');
        }}
        </script>
        """))
    
    def show_gradio_link(self, url: str):
        """Display the Gradio link prominently"""
        display(HTML(f"""
        <script>
        if (window.trinityOutputReady && window.showGradioLink) {{
            window.showGradioLink('{url}');
        }}
        if (window.updateStatusIndicator) {{
            window.updateStatusIndicator('running');
        }}
        </script>
        """))
    
    def show_launch_stats(self, stats: dict):
        """Display launch statistics"""
        display(HTML(f"""
        <script>
        if (window.trinityOutputReady && window.showLaunchStats) {{
            window.showLaunchStats({json.dumps(stats)});
        }}
        </script>
        """))
    
    def categorize_line(self, line: str) -> str:
        """Categorize output line for styling"""
        line_lower = line.lower()
        
        if any(keyword in line_lower for keyword in ['error', 'failed', 'exception', 'traceback']):
            return 'error'
        elif any(keyword in line_lower for keyword in ['warning', 'warn', 'deprecated', 'futurewarning']):
            return 'warning'
        elif any(keyword in line_lower for keyword in ['success', 'completed', 'ready', 'loaded', 'startup time']):
            return 'success'
        elif any(keyword in line_lower for keyword in ['gradio', 'running on', 'public url']):
            return 'gradio'
        else:
            return 'info'
    
    def extract_startup_stats(self, line: str) -> Optional[dict]:
        """Extract startup statistics from output"""
        if 'Startup time:' in line:
            # Extract timing information
            startup_match = re.search(r'Startup time: ([\d.]+)s', line)
            if startup_match:
                return {
                    'startup': startup_match.group(1) + 's',
                    'memory': 'Loading...',
                    'model': 'Initializing...'
                }
        elif 'Model loaded' in line:
            # Extract model loading time
            model_match = re.search(r'Model loaded in ([\d.]+)s', line)
            if model_match:
                return {
                    'startup': 'Complete',
                    'memory': 'Optimized',
                    'model': 'Loaded in ' + model_match.group(1) + 's'
                }
        return None
    
    def launch_with_styled_output(self, config: dict, timeout: int = 600) -> bool:
        """Launch WebUI with enhanced styled output and auto-scroll"""
        webui_choice = config.get('webui_choice', 'A1111')
        
        if not self.validate_environment(webui_choice):
            return False
        
        webui_path = Path(f'/content/{webui_choice}')
        venv_python = webui_path / 'venv' / 'bin' / 'python'
        args_list = self.construct_launch_args(config)
        
        launch_cmd = [str(venv_python), 'launch.py'] + args_list
        
        # Create styled output container
        self.create_styled_output_container()
        
        self.add_output_line(f"🚀 Launching {webui_choice} with Trinity enhanced styling", "success")
        self.add_output_line(f"🔧 Launch arguments: {' '.join(args_list)}", "info")
        self.add_output_line("📡 Initializing and waiting for Gradio public URL...", "info")
        self.add_output_line("🎨 Auto-scroll enabled - latest output will appear automatically", "info")
        
        # Set environment with matplotlib fix
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
                        self.add_output_line("❌ WebUI process ended unexpectedly", "error")
                        break
                    time.sleep(0.1)
                    continue
                
                # Categorize and add line with enhanced styling
                line_type = self.categorize_line(line)
                self.add_output_line(line.strip(), line_type)
                
                # Check for startup stats
                stats = self.extract_startup_stats(line)
                if stats:
                    self.show_launch_stats(stats)
                
                # Check for Gradio URL
                gradio_url = self.detect_gradio_url(line)
                if gradio_url:
                    self.add_output_line("🎉 GRADIO URL DETECTED!", "success")
                    self.add_output_line("", "info")
                    self.add_output_line("Your WebUI is now accessible:", "success")
                    self.show_gradio_link(gradio_url)
                    self.add_output_line("Click the link above to access your Stable Diffusion WebUI", "success")
                    self.add_output_line("🔄 Output will continue to auto-scroll with latest updates", "info")
                    url_found = True
                    break
            
            if not url_found:
                self.add_output_line(f"❌ No Gradio URL found within {timeout} seconds", "error")
                self.add_output_line("💡 The WebUI may still be starting. Check the output above.", "warning")
                process.terminate()
                return False
            
            # Continue showing output with auto-scroll
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        if process.poll() is not None:
                            break
                        time.sleep(0.1)
                        continue
                    
                    line_type = self.categorize_line(line)
                    self.add_output_line(line.strip(), line_type)
                    
                    # Show additional stats if found
                    stats = self.extract_startup_stats(line)
                    if stats:
                        self.show_launch_stats(stats)
                    
            except KeyboardInterrupt:
                self.add_output_line("✅ WebUI shutdown requested by user", "info")
                process.terminate()
            
            return True
            
        except Exception as e:
            self.add_output_line(f"❌ Launch failed: {e}", "error")
            return False

def launch_webui_with_trinity_styling():
    """Launch WebUI with Trinity's repository-based styling and auto-scroll"""
    project_root = Path('/content/TrinityUI')
    launcher = TrinityLauncher(project_root)
    
    config = launcher.load_config()
    if not config:
        print("❌ Failed to load configuration. Please run Cell 2 first.")
        return False
    
    webui_choice = config.get('webui_choice', 'A1111')
    print(f"🚀 Starting {webui_choice} with Trinity enhanced styling...")
    
    return launcher.launch_with_styled_output(config)

if __name__ == "__main__":
    launch_webui_with_trinity_styling()
