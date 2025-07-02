"""
TrinityUI WebUI-Specific Dependency Manager
Handles different dependency requirements for each WebUI
Version: 1.0.0 - WebUI-specific dependency management
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class WebUIDependencyManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.webui_root = Path('/content')
        self.log_file = project_root / 'trinity_unified.log'
        
        # WebUI-specific requirements
        self.webui_specs = {
            'A1111': {
                'python_version': '3.10',
                'pytorch_version': '2.1.2+cu121',
                'torchvision_version': '0.16.2+cu121',
                'torchaudio_version': '2.1.2+cu121',
                'xformers_version': '0.0.23.post1',
                'pytorch_index': 'https://download.pytorch.org/whl/cu121',
                'additional_packages': [
                    'transformers==4.30.2',
                    'safetensors==0.4.2',
                    'accelerate',
                    'diffusers'
                ]
            },
            'Forge': {
                'python_version': '3.11', 
                'pytorch_version': '2.3.1+cu121',
                'torchvision_version': '0.18.1+cu121',
                'torchaudio_version': '2.3.1+cu121',
                'xformers_version': '0.0.27.post2',
                'pytorch_index': 'https://download.pytorch.org/whl/cu121',
                'additional_packages': [
                    'transformers==4.46.1',
                    'safetensors',
                    'accelerate',
                    'diffusers'
                ]
            },
            'ComfyUI': {
                'python_version': '3.10',
                'pytorch_version': '2.1.2+cu121', 
                'torchvision_version': '0.16.2+cu121',
                'torchaudio_version': '2.1.2+cu121',
                'xformers_version': '0.0.23.post1',
                'pytorch_index': 'https://download.pytorch.org/whl/cu121',
                'additional_packages': [
                    'transformers==4.37.2',
                    'safetensors==0.4.2',
                    'accelerate',
                    'diffusers'
                ]
            },
            'ReForge': {
                'python_version': '3.11',
                'pytorch_version': '2.3.1+cu121',
                'torchvision_version': '0.18.1+cu121', 
                'torchaudio_version': '2.3.1+cu121',
                'xformers_version': '0.0.27.post2',
                'pytorch_index': 'https://download.pytorch.org/whl/cu121',
                'additional_packages': [
                    'transformers',
                    'safetensors',
                    'accelerate',
                    'diffusers'
                ]
            }
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages to unified log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [v1.0.0] [{level}] [WEBUI-DEPS] {message}\n"
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
        print(f"[{level}] {message}")
    
    def validate_webui_environment(self, webui_choice: str) -> Tuple[bool, str]:
        """Validate that WebUI environment exists and is properly set up"""
        if webui_choice not in self.webui_specs:
            return False, f"Unsupported WebUI: {webui_choice}"
        
        webui_path = self.webui_root / webui_choice
        venv_path = webui_path / 'venv'
        venv_python = venv_path / 'bin' / 'python'
        venv_pip = venv_path / 'bin' / 'pip'
        
        if not webui_path.exists():
            return False, f"WebUI directory not found: {webui_path}"
        
        if not venv_path.exists():
            return False, f"Virtual environment not found: {venv_path}"
        
        if not venv_python.exists():
            return False, f"Python executable not found: {venv_python}"
        
        if not venv_pip.exists():
            return False, f"Pip executable not found: {venv_pip}"
        
        # Check Python version
        try:
            result = subprocess.run(
                [str(venv_python), '--version'], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_output = result.stdout.strip()
                expected_version = self.webui_specs[webui_choice]['python_version']
                if expected_version not in version_output:
                    return False, f"Python version mismatch. Expected {expected_version}, got: {version_output}"
            else:
                return False, f"Could not check Python version: {result.stderr}"
        except Exception as e:
            return False, f"Error checking Python version: {e}"
        
        return True, "Environment validation passed"
    
    def check_current_dependencies(self, webui_choice: str) -> Dict[str, str]:
        """Check currently installed dependency versions"""
        webui_path = self.webui_root / webui_choice
        venv_python = webui_path / 'venv' / 'bin' / 'python'
        
        dependencies = {}
        
        packages_to_check = [
            ('torch', 'import torch; print(torch.__version__)'),
            ('torchvision', 'import torchvision; print(torchvision.__version__)'),
            ('xformers', 'import xformers; print(xformers.__version__)'),
            ('transformers', 'import transformers; print(transformers.__version__)'),
            ('safetensors', 'import safetensors; print(safetensors.__version__)')
        ]
        
        for package_name, check_command in packages_to_check:
            try:
                result = subprocess.run(
                    [str(venv_python), '-c', check_command],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    dependencies[package_name] = result.stdout.strip()
                else:
                    dependencies[package_name] = 'Not installed'
            except Exception:
                dependencies[package_name] = 'Error checking'
        
        return dependencies
    
    def install_webui_dependencies(self, webui_choice: str) -> bool:
        """Install correct dependencies for specific WebUI"""
        self.log(f"Installing dependencies for {webui_choice}", "INFO")
        
        # Validate environment first
        is_valid, message = self.validate_webui_environment(webui_choice)
        if not is_valid:
            self.log(f"Environment validation failed: {message}", "ERROR")
            return False
        
        webui_path = self.webui_root / webui_choice
        venv_pip = webui_path / 'venv' / 'bin' / 'pip'
        venv_python = webui_path / 'venv' / 'bin' / 'python'
        
        specs = self.webui_specs[webui_choice]
        
        try:
            # Step 1: Upgrade pip and basic tools
            self.log("Upgrading pip and setuptools", "INFO")
            upgrade_cmd = [
                str(venv_pip), 'install', '--upgrade', 
                'pip', 'setuptools', 'wheel'
            ]
            result = subprocess.run(upgrade_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                self.log(f"Pip upgrade warning: {result.stderr[:200]}", "WARNING")
            
            # Step 2: Uninstall conflicting packages
            self.log("Removing existing PyTorch/xFormers installations", "INFO")
            uninstall_packages = ['torch', 'torchvision', 'torchaudio', 'xformers']
            
            for package in uninstall_packages:
                uninstall_cmd = [str(venv_pip), 'uninstall', '-y', package]
                subprocess.run(uninstall_cmd, capture_output=True, text=True, timeout=60)
            
            # Step 3: Install PyTorch stack
            self.log(f"Installing PyTorch {specs['pytorch_version']} for {webui_choice}", "INFO")
            pytorch_cmd = [
                str(venv_pip), 'install',
                f"torch=={specs['pytorch_version']}",
                f"torchvision=={specs['torchvision_version']}",
                f"torchaudio=={specs['torchaudio_version']}",
                '--index-url', specs['pytorch_index'],
                '--force-reinstall'
            ]
            
            result = subprocess.run(pytorch_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                self.log(f"PyTorch installation failed: {result.stderr[:300]}", "ERROR")
                return False
            else:
                self.log("PyTorch installation successful", "SUCCESS")
            
            # Step 4: Install xFormers
            self.log(f"Installing xFormers {specs['xformers_version']} for {webui_choice}", "INFO")
            xformers_cmd = [
                str(venv_pip), 'install', 
                f"xformers=={specs['xformers_version']}",
                '--force-reinstall'
            ]
            
            result = subprocess.run(xformers_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.log(f"xFormers installation failed: {result.stderr[:300]}", "ERROR")
                # Try without version specification
                self.log("Trying xFormers installation without version pinning", "INFO")
                fallback_cmd = [str(venv_pip), 'install', 'xformers', '--force-reinstall']
                result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.log("xFormers fallback installation also failed", "ERROR")
                    return False
            
            self.log("xFormers installation successful", "SUCCESS")
            
            # Step 5: Install additional packages
            self.log("Installing additional packages", "INFO")
            for package in specs['additional_packages']:
                package_cmd = [str(venv_pip), 'install', package, '--upgrade']
                result = subprocess.run(package_cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    self.log(f"Successfully installed {package}", "SUCCESS")
                else:
                    self.log(f"Failed to install {package}: {result.stderr[:100]}", "WARNING")
            
            # Step 6: Install WebUI requirements if they exist
            requirements_files = [
                webui_path / 'requirements_versions.txt',
                webui_path / 'requirements.txt'
            ]
            
            for req_file in requirements_files:
                if req_file.exists():
                    self.log(f"Installing from {req_file.name}", "INFO")
                    req_cmd = [str(venv_pip), 'install', '-r', str(req_file)]
                    result = subprocess.run(req_cmd, capture_output=True, text=True, timeout=600)
                    
                    if result.returncode == 0:
                        self.log(f"Successfully installed from {req_file.name}", "SUCCESS")
                    else:
                        self.log(f"Warning installing from {req_file.name}: {result.stderr[:200]}", "WARNING")
                    break
            
            # Step 7: Verify installation
            self.log("Verifying dependency installation", "INFO")
            verify_cmd = [
                str(venv_python), '-c',
                '''
import torch
import xformers
print(f"PyTorch: {torch.__version__}")
print(f"xFormers: {xformers.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"xFormers CUDA: {hasattr(xformers.ops, 'memory_efficient_attention')}")
'''
            ]
            
            result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log("Dependency verification successful", "SUCCESS")
                self.log(f"Verification output:\n{result.stdout}", "INFO")
                return True
            else:
                self.log(f"Dependency verification failed: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Dependency installation timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Dependency installation failed with exception: {e}", "ERROR")
            return False
    
    def create_dependency_report(self, webui_choice: str) -> str:
        """Create detailed dependency report"""
        report = []
        report.append("=" * 70)
        report.append(f"TRINITY WEBUI DEPENDENCY REPORT - {webui_choice}")
        report.append("=" * 70)
        
        # Expected specifications
        if webui_choice in self.webui_specs:
            specs = self.webui_specs[webui_choice]
            report.append("EXPECTED SPECIFICATIONS:")
            report.append(f"  Python Version: {specs['python_version']}")
            report.append(f"  PyTorch Version: {specs['pytorch_version']}")
            report.append(f"  xFormers Version: {specs['xformers_version']}")
            report.append("")
        
        # Environment validation
        is_valid, message = self.validate_webui_environment(webui_choice)
        report.append(f"ENVIRONMENT VALIDATION: {'✅ PASSED' if is_valid else '❌ FAILED'}")
        if not is_valid:
            report.append(f"  Error: {message}")
        report.append("")
        
        # Current dependencies
        if is_valid:
            current_deps = self.check_current_dependencies(webui_choice)
            report.append("CURRENT INSTALLATIONS:")
            for package, version in current_deps.items():
                status = "✅" if version not in ['Not installed', 'Error checking'] else "❌"
                report.append(f"  {package}: {status} {version}")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        if is_valid and webui_choice in self.webui_specs:
            current_deps = self.check_current_dependencies(webui_choice)
            specs = self.webui_specs[webui_choice]
            
            needs_update = False
            if current_deps.get('torch', '').split('+')[0] != specs['pytorch_version'].split('+')[0]:
                report.append(f"  📦 Update PyTorch to {specs['pytorch_version']}")
                needs_update = True
            
            if current_deps.get('xformers', '') != specs['xformers_version']:
                report.append(f"  📦 Update xFormers to {specs['xformers_version']}")
                needs_update = True
            
            if not needs_update:
                report.append("  ✅ All dependencies appear to be correct")
        else:
            report.append("  🔧 Run dependency installation to fix issues")
        
        report.append("")
        report.append("=" * 70)
        
        return '\n'.join(report)

def fix_webui_dependencies(webui_choice: str) -> bool:
    """Main function to fix dependencies for specific WebUI"""
    project_root = Path('/content/TrinityUI')
    manager = WebUIDependencyManager(project_root)
    
    print(f"🔧 Trinity WebUI Dependency Manager - {webui_choice}")
    print("=" * 70)
    
    # Show initial report
    initial_report = manager.create_dependency_report(webui_choice)
    print(initial_report)
    
    # Ask user confirmation
    print(f"\n🔄 Ready to install {webui_choice}-specific dependencies.")
    print("This will reinstall PyTorch and xFormers with correct versions.")
    
    # Install dependencies
    print(f"\n🚀 Starting dependency installation for {webui_choice}...")
    success = manager.install_webui_dependencies(webui_choice)
    
    if success:
        print(f"\n✅ Dependency installation completed successfully for {webui_choice}!")
        
        # Show updated report
        updated_report = manager.create_dependency_report(webui_choice)
        print("\nUPDATED DEPENDENCY REPORT:")
        print(updated_report)
        
        print(f"\n🎉 {webui_choice} is now ready to launch with proper xFormers support!")
        return True
    else:
        print(f"\n❌ Dependency installation failed for {webui_choice}")
        print("💡 Check the log output above for detailed error information")
        return False

if __name__ == "__main__":
    import sys
    webui_choice = sys.argv[1] if len(sys.argv) > 1 else 'A1111'
    fix_webui_dependencies(webui_choice)
