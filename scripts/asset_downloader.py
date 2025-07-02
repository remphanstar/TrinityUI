"""
TrinityUI Asset Download Manager
Handles model, VAE, ControlNet, and LoRA downloads
"""
import json
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .aria2c_manager import Aria2cManager

class AssetDownloader:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.aria2c = Aria2cManager()
        
    def load_model_data(self, is_xl: bool = False) -> Tuple[Dict, Dict, Dict, Dict]:
        """Load model data from repository files"""
        try:
            if is_xl:
                data_file = self.project_root / 'scripts' / '_xl-models-data.py'
            else:
                data_file = self.project_root / 'scripts' / '_models-data.py'
            
            if not data_file.exists():
                print(f"❌ Model data file not found: {data_file}")
                return {}, {}, {}, {}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            namespace = {}
            exec(content, namespace)
            
            model_list = namespace.get('model_list', {})
            vae_list = namespace.get('vae_list', {})
            controlnet_list = namespace.get('controlnet_list', {})
            lora_list = namespace.get('lora_list', {})
            
            print(f"📊 Loaded data: {len(model_list)} models, {len(vae_list)} VAEs, {len(controlnet_list)} ControlNets, {len(lora_list)} LoRAs")
            
            return model_list, vae_list, controlnet_list, lora_list
            
        except Exception as e:
            print(f"❌ Error loading model data: {e}")
            return {}, {}, {}, {}
    
    def get_webui_directories(self, webui_choice: str) -> Dict[str, Path]:
        """Get correct directory structure for different WebUIs"""
        webui_path = Path(f'/content/{webui_choice}')
        
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
    
    def download_selected_assets(self, config: Dict[str, Any]) -> bool:
        """Download only the selected assets with aria2c acceleration"""
        webui_choice = config.get('webui_choice', 'A1111')
        is_xl = config.get('sd_version') == 'SDXL'
        
        selected_models = config.get('selected_models', [])
        selected_vaes = config.get('selected_vaes', [])
        selected_controlnets = config.get('selected_controlnets', [])
        selected_loras = config.get('selected_loras', [])
        
        print(f"🎯 Downloading selected assets for {webui_choice}")
        print(f"📋 Your selections:")
        print(f"   Models: {selected_models}")
        print(f"   VAEs: {selected_vaes}")
        print(f"   ControlNets: {selected_controlnets}")
        print(f"   LoRAs: {selected_loras}")
        
        if not any([selected_models, selected_vaes, selected_controlnets, selected_loras]):
            print("✅ No assets selected for download")
            return True
        
        # Load model data
        model_list, vae_list, controlnet_list, lora_list = self.load_model_data(is_xl)
        
        if not any([model_list, vae_list, controlnet_list, lora_list]):
            print("❌ Failed to load model data files")
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
                    print(f"📦 Found selected {asset_type}: {item_name}")
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
            print("❌ No valid download URLs found for selections")
            return False
        
        print(f"\n📥 Starting high-speed download of {len(download_tasks)} files...")
        
        # Download with aria2c acceleration
        success_count = 0
        total_count = len(download_tasks)
        
        for i, task in enumerate(download_tasks, 1):
            print(f"🔄 [{i}/{total_count}] Downloading {task['type']} from '{task['selection']}': {task['filename']}")
            
            # Check if file already exists
            file_path = task['path'] / task['filename']
            if file_path.exists() and file_path.stat().st_size > 1024*1024:  # > 1MB
                print(f"   ✅ Already exists: {task['filename']}")
                success_count += 1
                continue
            
            success, message = self.aria2c.download_file(
                task['url'], 
                task['path'], 
                task['filename']
            )
            
            if success:
                success_count += 1
                print(f"   ✅ {message}")
            else:
                print(f"   ❌ {message}")
        
        print(f"\n📊 Download Summary: {success_count}/{total_count} assets downloaded successfully")
        return success_count > 0
