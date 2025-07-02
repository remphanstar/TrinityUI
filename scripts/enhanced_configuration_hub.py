"""
Enhanced Trinity Configuration Hub with Installation Integration
Version: 1.4.3 - Fixed text color and cell completion issues
"""

import gradio as gr
import os
import sys
import json
import ast
import threading
import time
import requests
from pathlib import Path
from datetime import datetime

# --- Configuration ---
def get_project_root():
    try:
        root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        if (root / 'scripts').exists(): return root
    except: pass
    return Path(__file__).parent.parent

PROJECT_ROOT = get_project_root()
scripts_path = PROJECT_ROOT / 'scripts'
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(scripts_path))

# Import installation manager components
try:
    from scripts.installation_manager import InstallationProgressTracker, run_installation
except ImportError:
    print("Warning: Could not import installation manager")
    InstallationProgressTracker = None
    run_installation = None

TRINITY_VERSION = "1.4.3"
CONFIG_PATH = PROJECT_ROOT / "trinity_config.json"
LOG_FILE = PROJECT_ROOT / "trinity_unified.log"

def log_to_unified(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [v{TRINITY_VERSION}] [{level}] [CONFIG-HUB] {message}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f: f.write(log_entry)
    except: pass

def load_html_from_repo(html_file):
    """Load HTML content from repository"""
    base_url = "https://raw.githubusercontent.com/remphanstar/TrinityUI/main/HTML"
    try:
        response = requests.get(f"{base_url}/{html_file}", timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return f"<div>Failed to load {html_file}</div>"
    except Exception as e:
        return f"<div>Error loading {html_file}: {e}</div>"

# --- Data Loading ---
def read_model_data(file_path, data_type):
    """Version: 1.1.0 - Reimplemented with ast.literal_eval() for robustness"""
    if not file_path.exists(): 
        return [f"Error: Data file not found at {file_path}"]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f: 
            content = f.read()
        
        key_map = {'model': 'model_list', 'vae': 'vae_list', 'cnet': 'controlnet_list', 'lora': 'lora_list'}
        key = key_map.get(data_type)
        if not key: 
            return [f"Invalid data type: {data_type}"]
        
        start_pattern = f"{key} = {{"
        start_index = content.find(start_pattern)
        if start_index == -1: 
            return [f"Error: No dictionary found for '{key}'"]
        
        dict_start_index = start_index + len(start_pattern) - 1
        brace_count, end_index = 1, -1
        
        for i, char in enumerate(content[dict_start_index+1:], 1):
            if char == '{': brace_count += 1
            elif char == '}': 
                brace_count -= 1
                if brace_count == 0:
                    end_index = dict_start_index + i + 1
                    break
        
        if end_index == -1: 
            return ["Error: Could not find closing brace for dictionary."]
        
        dict_str = content[dict_start_index:end_index]
        data_dict = ast.literal_eval(dict_str)
        names = list(data_dict.keys())
        
        return ["none"] + names if names else ["none"]
    
    except Exception as e:
        return [f"Error parsing {file_path} for '{data_type}': {e}"]

# --- Global State ---
webui_selection = { "A1111": "--api --xformers --no-half-vae", "ComfyUI": "--listen", "Forge": "--xformers", "ReForge": "--xformers" }
model_data_file = scripts_path / '_models-data.py'
xl_model_data_file = scripts_path / '_xl-models-data.py'

# Installation state
installation_in_progress = False
installation_tracker = None
current_config = None
progress_displays = {}

def update_model_lists_for_version(is_xl):
    data_file = xl_model_data_file if is_xl else model_data_file
    try:
        model_options = read_model_data(data_file, 'model')
        vae_options = read_model_data(data_file, 'vae')
        controlnet_options = read_model_data(data_file, 'cnet')
        lora_options = read_model_data(data_file, 'lora')
        
        if is_xl:
            default_model = next((opt for opt in model_options if "xl" in opt.lower()), model_options[1] if len(model_options) > 1 else "none")
            default_vae = next((opt for opt in vae_options if "xl" in opt.lower()), vae_options[1] if len(vae_options) > 1 else "none")
        else:
            default_model = next((opt for opt in model_options if "1.5" in opt.lower() or "v1-5" in opt.lower()), model_options[1] if len(model_options) > 1 else "none")
            default_vae = next((opt for opt in vae_options if "840000" in opt.lower()), vae_options[1] if len(vae_options) > 1 else "none")
        
        return (
            gr.update(choices=model_options, value=[default_model] if default_model != "none" else []),
            gr.update(choices=vae_options, value=[default_vae] if default_vae != "none" else []),
            gr.update(choices=controlnet_options, value=[]),
            gr.update(choices=lora_options, value=[])
        )
    except Exception as e:
        log_to_unified(f"Error updating lists: {e}", "ERROR")
        return (gr.update(), gr.update(), gr.update(), gr.update())

def update_progress_displays(update_type, data):
    """Update progress displays globally"""
    global progress_displays
    try:
        if update_type == "dependency_progress" and "dependency" in progress_displays:
            # Use light text color for dark background
            progress_displays["dependency"].update(value=f'<div style="color: #e8e8e8; font-family: monospace; white-space: pre-wrap;">{data}</div>')
        elif update_type == "asset_progress" and "asset" in progress_displays:
            asset_html = ""
            for asset in data:
                status_icon = {"success": "✅", "error": "❌", "downloading": "⬇️", "pending": "⏳"}.get(asset.get('status', 'pending'), "⏳")
                asset_html += f'<div style="padding: 5px; border-bottom: 1px solid #444; color: #e8e8e8;"><span style="margin-right: 10px;">{status_icon}</span>{asset["name"]}</div>'
            progress_displays["asset"].update(value=f'<div style="max-height: 300px; overflow-y: auto; color: #e8e8e8;">{asset_html}</div>')
        elif update_type == "completion" and "completion" in progress_displays:
            progress_displays["completion"].update(visible=data)
    except Exception as e:
        log_to_unified(f"Error updating progress displays: {e}", "ERROR")

def run_installation_thread(config_data):
    """Run installation in background thread"""
    global installation_in_progress, installation_tracker
    
    try:
        installation_in_progress = True
        print("📝 Starting installation thread...")
        
        if InstallationProgressTracker and run_installation:
            # Create progress tracker with callbacks
            installation_tracker = InstallationProgressTracker(
                notebook_callback=lambda msg: print(f"📝 {msg}", end=''),
                gradio_callback=update_progress_displays
            )
            
            print("📝 Installation tracker created, starting installation...")
            
            # Run installation
            success = run_installation(config_data, installation_tracker)
            
            print(f"📝 Installation completed with success: {success}")
            return success
        else:
            log_to_unified("Installation manager not available", "ERROR")
            print("❌ Installation manager not available")
            return False
        
    except Exception as e:
        log_to_unified(f"Installation thread failed: {e}", "ERROR")
        print(f"❌ Installation thread failed: {e}")
        return False
    finally:
        installation_in_progress = False
        print("📝 Installation thread finished")

def save_config_and_install(webui_choice, sd_version, models, vaes, controlnets, loras, arguments, theme_accent, civitai_token, ngrok_token, tunnel_choice):
    """Save configuration and start installation"""
    global current_config, installation_in_progress, progress_displays
    
    print(f"📝 Save button clicked for {webui_choice}")
    
    if installation_in_progress:
        return (
            gr.update(value="⚠️ Installation already in progress..."),
            gr.update(visible=True),
            gr.update(value='<div style="color: #ffa500; padding: 20px; text-align: center;">Installation in progress...</div>'),
            gr.update(value='<div style="color: #ffa500; padding: 20px; text-align: center;">Please wait...</div>')
        )
    
    session_id = f"TR_{int(time.time())}"
    config_data = {
        "webui_choice": webui_choice, 
        "sd_version": "SDXL" if sd_version else "SD1.5",
        "selected_models": models, 
        "selected_vaes": vaes,
        "selected_controlnets": controlnets, 
        "selected_loras": loras,
        "custom_args": arguments, 
        "theme": theme_accent, 
        "civitai_token": civitai_token,
        "ngrok_token": ngrok_token, 
        "tunnel_choice": tunnel_choice, 
        "session_id": session_id,
    }
    
    try:
        # Save configuration
        with open(CONFIG_PATH, "w", encoding='utf-8') as f: 
            json.dump(config_data, f, indent=4)
        
        current_config = config_data
        print(f"📝 Configuration saved to {CONFIG_PATH}")
        
        # Start installation in background thread
        installation_thread = threading.Thread(
            target=run_installation_thread, 
            args=(config_data,),
            daemon=True
        )
        installation_thread.start()
        print("📝 Installation thread started")
        
        success_msg = f"✅ Config saved for {webui_choice}. Installation started in background..."
        log_to_unified(success_msg, "SUCCESS")
        
        return (
            gr.update(value=success_msg),
            gr.update(visible=True),
            gr.update(value='<div style="color: #4CAF50; padding: 20px; text-align: center; font-weight: bold;">Starting dependency installation...</div>'),
            gr.update(value='<div style="color: #e8e8e8; padding: 20px; text-align: center;">Preparing asset downloads...</div>')
        )
        
    except Exception as e:
        error_msg = f"❌ Failed to save config: {e}"
        log_to_unified(error_msg, "ERROR")
        print(f"❌ {error_msg}")
        return (
            gr.update(value=error_msg),
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value="")
        )

def create_trinity_interface():
    """Create the enhanced Trinity interface with installation integration"""
    
    with gr.Blocks(theme=gr.themes.Base(), title="Trinity Configuration & Installation Hub") as interface:
        gr.Markdown(f"# 🚀 Trinity Configuration & Installation Hub v{TRINITY_VERSION}")
        gr.Markdown("Configure your WebUI settings and automatically start installation")
        
        with gr.Row():
            webui_dropdown = gr.Dropdown(
                choices=list(webui_selection.keys()), 
                label="Select WebUI", 
                value="A1111",
                info="Choose your preferred Stable Diffusion WebUI"
            )
            is_xl_checkbox = gr.Checkbox(
                label="Use SDXL Models", 
                value=False,
                info="Enable for SDXL (1024x1024) model support"
            )
            tunnel_choice = gr.Radio(
                choices=["Gradio", "ngrok"], 
                label="Tunneling Service", 
                value="Gradio",
                info="Service for public URL generation"
            )
        
        with gr.Accordion("Model Selection", open=True):
            gr.Markdown("### Select models, VAEs, ControlNets, and LoRAs to download")
            
            with gr.Row():
                with gr.Column():
                    model_cbg = gr.CheckboxGroup([], label="Checkpoint Model(s)")
                    vae_cbg = gr.CheckboxGroup([], label="VAE(s)")
                with gr.Column():
                    controlnet_cbg = gr.CheckboxGroup([], label="ControlNet(s)")
                    lora_cbg = gr.CheckboxGroup([], label="LoRA(s)")
        
        with gr.Accordion("Advanced & Secrets", open=False):
            arguments_textbox = gr.Textbox(
                label="Custom Launch Arguments", 
                lines=1,
                placeholder="Additional arguments for WebUI launch",
                info="Custom arguments will be added to the launch command"
            )
            
            with gr.Row():
                theme_dropdown = gr.Dropdown(
                    choices=["Default", "Dark", "Light"], 
                    label="Theme", 
                    value="Default"
                )
                civitai_token = gr.Textbox(
                    label="Civitai API Token", 
                    type="password",
                    placeholder="Optional: For downloading from Civitai"
                )
                ngrok_token = gr.Textbox(
                    label="Ngrok Token", 
                    type="password",
                    placeholder="Optional: For ngrok tunneling"
                )
        
        # Enhanced save button
        save_button = gr.Button(
            "💾 Save Configuration & Start Installation", 
            variant="primary", 
            size="lg",
            elem_id="save-install-button"
        )
        
        status_display = gr.Markdown("Ready to configure and install.")
        
        # Progress display section
        with gr.Accordion("📊 Installation Progress", open=False, visible=False) as progress_accordion:
            gr.Markdown("### Real-time Installation Progress")
            
            with gr.Tab("Dependency Installation"):
                dependency_progress = gr.HTML(
                    value='<div style="padding: 20px; text-align: center; color: #e8e8e8; background: #2d2d2d; border-radius: 8px;">Waiting for installation to start...</div>',
                    elem_id="dependency-progress"
                )
            
            with gr.Tab("Asset Downloads"):
                asset_progress = gr.HTML(
                    value='<div style="padding: 20px; text-align: center; color: #e8e8e8; background: #2d2d2d; border-radius: 8px;">Waiting for downloads to start...</div>',
                    elem_id="asset-progress"
                )
        
        # Store progress displays globally for updates
        global progress_displays
        progress_displays = {
            "dependency": dependency_progress,
            "asset": asset_progress,
            "completion": progress_accordion
        }
        
        # Event handlers
        is_xl_checkbox.change(
            fn=update_model_lists_for_version, 
            inputs=[is_xl_checkbox], 
            outputs=[model_cbg, vae_cbg, controlnet_cbg, lora_cbg]
        )
        
        webui_dropdown.change(
            fn=lambda w: gr.update(value=webui_selection.get(w, "")), 
            inputs=[webui_dropdown], 
            outputs=[arguments_textbox]
        )
        
        # Save button click handler
        save_button.click(
            fn=save_config_and_install,
            inputs=[
                webui_dropdown, is_xl_checkbox, model_cbg, vae_cbg, 
                controlnet_cbg, lora_cbg, arguments_textbox, theme_dropdown, 
                civitai_token, ngrok_token, tunnel_choice
            ],
            outputs=[status_display, progress_accordion, dependency_progress, asset_progress]
        )
        
        # Initialize model lists on load
        interface.load(
            fn=lambda: update_model_lists_for_version(False), 
            outputs=[model_cbg, vae_cbg, controlnet_cbg, lora_cbg]
        )
    
    return interface

def launch_trinity_configuration_hub():
    """Launch the Trinity Configuration & Installation Hub"""
    try:
        log_to_unified("Initializing Enhanced Config Hub with Installation...")
        interface = create_trinity_interface()
        port = int(os.environ.get('TRINITY_CONFIG_PORT', 7860))
        
        print(f"🚀 Launching Trinity Configuration Hub on port {port}")
        print("🔧 Installation will run in background after configuration save")
        print("📊 Progress will be visible in the Installation Progress tab")
        
        interface.launch(
            server_name="0.0.0.0", 
            server_port=port, 
            share=True,
            quiet=False, 
            show_error=True, 
            inline=False,
            favicon_path=None
        )
        
    except Exception as e:
        log_to_unified(f"Failed to launch Enhanced Config Hub: {e}", "ERROR")
        raise

if __name__ == "__main__":
    launch_trinity_configuration_hub()
