"""
Enhanced Trinity Configuration Hub with Installation Integration
Version: 1.5.1 - Fixed Gradio component update methods
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

TRINITY_VERSION = "1.5.1"
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

# Global progress components - store references for direct updates
progress_state = {
    "dependency_component": None,
    "asset_component": None,
    "accordion_visible": False,
    "accordion_open": False
}

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

def gradio_progress_callback(update_type, data):
    """Callback for real-time Gradio progress updates"""
    global progress_state
    
    try:
        print(f"📊 [GRADIO] Progress update: {update_type}")
        
        if update_type == "dependency_progress":
            # Format dependency log for better readability
            formatted_data = str(data).replace('\n', '<br>') if data else "Starting..."
            html_content = f'''
            <div style="color: #e8e8e8; font-family: 'Courier New', monospace; 
                       background: #1a1a1a; padding: 15px; border-radius: 8px; 
                       max-height: 400px; overflow-y: auto; border: 1px solid #333;">
                {formatted_data}
            </div>
            '''
            # Store the updated content - will be returned by get_progress_updates
            progress_state["dependency_content"] = html_content
            print(f"📊 [GRADIO] Updated dependency progress display")
        
        elif update_type == "asset_progress":
            if isinstance(data, list):
                asset_html = ""
                for asset in data:
                    status_icon = {
                        "success": "✅", 
                        "error": "❌", 
                        "downloading": "⬇️", 
                        "pending": "⏳"
                    }.get(asset.get('status', 'pending'), "⏳")
                    
                    error_info = ""
                    if asset.get('error'):
                        error_info = f'<div style="color: #ff6b6b; font-size: 12px; margin-left: 35px; margin-top: 5px;">{asset["error"]}</div>'
                    
                    asset_html += f'''
                        <div style="padding: 10px; border-bottom: 1px solid #444; color: #e8e8e8;">
                            <div style="display: flex; align-items: center;">
                                <span style="margin-right: 15px; font-size: 18px;">{status_icon}</span>
                                <span style="font-family: 'Courier New', monospace; flex: 1;">{asset["name"]}</span>
                            </div>
                            {error_info}
                        </div>
                    '''
                
                if not asset_html:
                    asset_html = '<div style="color: #888; text-align: center; padding: 20px;">No assets being downloaded</div>'
                
                html_content = f'''
                <div style="max-height: 400px; overflow-y: auto; background: #1a1a1a; 
                           border-radius: 8px; border: 1px solid #333;">
                    {asset_html}
                </div>
                '''
                # Store the updated content
                progress_state["asset_content"] = html_content
                print(f"📊 [GRADIO] Updated asset progress display with {len(data)} items")
        
        elif update_type == "completion":
            progress_state["accordion_visible"] = True
            progress_state["accordion_open"] = True
            print(f"📊 [GRADIO] Set completion flags")
    
    except Exception as e:
        print(f"❌ [GRADIO] Error in progress callback: {e}")
        import traceback
        traceback.print_exc()

def get_progress_updates():
    """Function to return current progress state for Gradio updates"""
    global progress_state
    
    # Return current progress content and accordion state
    dependency_content = progress_state.get("dependency_content", 
        '<div style="padding: 20px; text-align: center; color: #888; background: #1a1a1a; border-radius: 8px; border: 1px solid #333;">Waiting for installation to start...</div>')
    
    asset_content = progress_state.get("asset_content",
        '<div style="padding: 20px; text-align: center; color: #888; background: #1a1a1a; border-radius: 8px; border: 1px solid #333;">Waiting for downloads to start...</div>')
    
    accordion_visible = progress_state.get("accordion_visible", False)
    accordion_open = progress_state.get("accordion_open", False)
    
    return (
        gr.update(visible=accordion_visible, open=accordion_open),
        gr.update(value=dependency_content),
        gr.update(value=asset_content)
    )

def run_installation_thread(config_data):
    """Run installation in background thread with real-time updates"""
    global installation_in_progress, installation_tracker, progress_state
    
    try:
        installation_in_progress = True
        print("📝 [THREAD] Starting installation thread...")
        
        # Set accordion visible immediately
        progress_state["accordion_visible"] = True
        progress_state["accordion_open"] = True
        
        if InstallationProgressTracker and run_installation:
            # Create progress tracker with callbacks
            installation_tracker = InstallationProgressTracker(
                notebook_callback=lambda msg: print(f"📝 [INSTALL] {msg}", end=''),
                gradio_callback=gradio_progress_callback
            )
            
            print("📝 [THREAD] Installation tracker created with Gradio callback")
            
            # Initial progress update
            gradio_progress_callback("dependency_progress", "Installation starting...")
            
            # Run installation
            success = run_installation(config_data, installation_tracker)
            
            print(f"📝 [THREAD] Installation completed with success: {success}")
            
            # Final progress update
            if success:
                gradio_progress_callback("completion", True)
                gradio_progress_callback("dependency_progress", "✅ Installation completed successfully!")
                print("✅ [THREAD] Installation completed successfully!")
            else:
                gradio_progress_callback("dependency_progress", "❌ Installation completed with errors")
                print("❌ [THREAD] Installation completed with errors")
            
            return success
        else:
            error_msg = "Installation manager not available"
            gradio_progress_callback("dependency_progress", f"❌ {error_msg}")
            log_to_unified(error_msg, "ERROR")
            print(f"❌ [THREAD] {error_msg}")
            return False
        
    except Exception as e:
        error_msg = f"Installation thread failed: {e}"
        gradio_progress_callback("dependency_progress", f"❌ {error_msg}")
        log_to_unified(error_msg, "ERROR")
        print(f"❌ [THREAD] {error_msg}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        installation_in_progress = False
        print("📝 [THREAD] Installation thread finished")

def save_config_and_install(webui_choice, sd_version, models, vaes, controlnets, loras, arguments, theme_accent, civitai_token, ngrok_token, tunnel_choice):
    """Save configuration and start installation with immediate progress feedback"""
    global current_config, installation_in_progress, progress_state
    
    print(f"📝 [SAVE] Save button clicked for {webui_choice}")
    print(f"📝 [SAVE] Selected items - Models: {len(models)}, VAEs: {len(vaes)}, ControlNets: {len(controlnets)}, LoRAs: {len(loras)}")
    
    if installation_in_progress:
        error_html = '<div style="color: #ffa500; padding: 20px; text-align: center; background: #2d2d2d; border-radius: 8px;">Installation already in progress...</div>'
        return (
            gr.update(value="⚠️ Installation already in progress..."),
            gr.update(visible=True, open=True),
            gr.update(value=error_html),
            gr.update(value=error_html)
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
        print(f"📝 [SAVE] Configuration saved to {CONFIG_PATH}")
        
        # Set progress state for immediate UI updates
        progress_state["accordion_visible"] = True
        progress_state["accordion_open"] = True
        
        # Initialize progress displays
        initial_dep_html = '''
        <div style="color: #4CAF50; padding: 20px; text-align: center; font-weight: bold; 
                   background: #1a1a1a; border-radius: 8px; border: 1px solid #4CAF50;">
            🔧 Initializing installation process...<br>
            <small style="color: #ccc;">Check notebook output below for detailed progress</small>
        </div>
        '''
        
        initial_asset_html = '''
        <div style="color: #e8e8e8; padding: 20px; text-align: center; 
                   background: #1a1a1a; border-radius: 8px; border: 1px solid #333;">
            ⏳ Waiting for dependency installation to complete...<br>
            <small style="color: #ccc;">Asset downloads will begin after dependencies are installed</small>
        </div>
        '''
        
        # Store initial content
        progress_state["dependency_content"] = initial_dep_html
        progress_state["asset_content"] = initial_asset_html
        
        # Start installation in background thread
        installation_thread = threading.Thread(
            target=run_installation_thread, 
            args=(config_data,),
            daemon=True,
            name="TrinityInstallationThread"
        )
        installation_thread.start()
        print("📝 [SAVE] Installation thread started")
        
        success_msg = f"✅ Config saved for {webui_choice}. Installation started with real-time progress!"
        log_to_unified(success_msg, "SUCCESS")
        
        return (
            gr.update(value=success_msg),
            gr.update(visible=True, open=True),
            gr.update(value=initial_dep_html),
            gr.update(value=initial_asset_html)
        )
        
    except Exception as e:
        error_msg = f"❌ Failed to save config: {e}"
        log_to_unified(error_msg, "ERROR")
        print(f"❌ [SAVE] {error_msg}")
        
        error_html = f'<div style="color: #ff6b6b; padding: 20px; background: #2d2d2d; border-radius: 8px;">{error_msg}</div>'
        return (
            gr.update(value=error_msg),
            gr.update(visible=False),
            gr.update(value=error_html),
            gr.update(value=error_html)
        )

def create_trinity_interface():
    """Create the enhanced Trinity interface with real-time installation progress"""
    global progress_state
    
    with gr.Blocks(theme=gr.themes.Base(), title="Trinity Configuration & Installation Hub") as interface:
        gr.Markdown(f"# 🚀 Trinity Configuration & Installation Hub v{TRINITY_VERSION}")
        gr.Markdown("Configure your WebUI settings and watch real-time installation progress")
        
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
            gr.Markdown("📝 **Progress updates in real-time - both here and in notebook output**")
            
            with gr.Tab("Dependency Installation"):
                dependency_progress = gr.HTML(
                    value='<div style="padding: 20px; text-align: center; color: #888; background: #1a1a1a; border-radius: 8px; border: 1px solid #333;">Waiting for installation to start...</div>',
                    elem_id="dependency-progress"
                )
            
            with gr.Tab("Asset Downloads"):
                asset_progress = gr.HTML(
                    value='<div style="padding: 20px; text-align: center; color: #888; background: #1a1a1a; border-radius: 8px; border: 1px solid #333;">Waiting for downloads to start...</div>',
                    elem_id="asset-progress"
                )
        
        # Auto-refresh progress every 2 seconds
        refresh_timer = gr.Timer(2.0)
        refresh_timer.tick(
            fn=get_progress_updates,
            outputs=[progress_accordion, dependency_progress, asset_progress]
        )
        
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
        log_to_unified("Initializing Enhanced Config Hub with Real-time Progress...")
        interface = create_trinity_interface()
        port = int(os.environ.get('TRINITY_CONFIG_PORT', 7860))
        
        print(f"🚀 Launching Trinity Configuration Hub on port {port}")
        print("🔧 Installation will show REAL-TIME progress in the interface")
        print("📊 Progress will be visible in both the interface and notebook output")
        print("⚠️ Installation starts ONLY when you click 'Save Configuration & Start Installation'")
        print("🎯 Only selected assets will be downloaded")
        
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
