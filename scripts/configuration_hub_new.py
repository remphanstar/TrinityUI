import gradio as gr
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import time
import ast

# --- Configuration ---
def get_project_root():
    try:
        root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        if (root / 'scripts').exists(): return root
    except: pass
    return Path(__file__).parent.parent

PROJECT_ROOT = get_project_root()
scripts_path = PROJECT_ROOT / 'scripts'
sys.path.insert(0, str(scripts_path))

# --- Data Loading ---
def read_model_data(file_path, data_type):
    if not file_path.exists(): return [f"Error: Data file not found at {file_path}"]
    try:
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        key_map = {'model': 'model_list', 'vae': 'vae_list', 'cnet': 'controlnet_list', 'lora': 'lora_list'}
        key = key_map.get(data_type)
        if not key: return [f"Invalid data type: {data_type}"]
        start_pattern = f"{key} = {{"
        start_index = content.find(start_pattern)
        if start_index == -1: return [f"Error: No dictionary found for '{key}'"]
        dict_start_index = start_index + len(start_pattern) - 1
        brace_count, end_index = 0, -1
        for i, char in enumerate(content[dict_start_index:]):
            if char == '{': brace_count += 1
            elif char == '}': brace_count -= 1
            if brace_count == 0:
                end_index = dict_start_index + i + 1
                break
        if end_index == -1: return ["Error: Could not find closing brace for dictionary."]
        dict_str = content[dict_start_index:end_index]
        data_dict = ast.literal_eval(dict_str)
        names = list(data_dict.keys())
        return ["none"] + names if names else ["none"]
    except Exception as e:
        return [f"Error parsing {file_path} for '{data_type}': {e}"]

# --- Constants & State ---
webui_selection = { "A1111": "--api --xformers --no-half-vae", "ComfyUI": "--listen", "Forge": "--xformers", "ReForge": "--xformers" }
model_data_file = scripts_path / '_models-data.py'
xl_model_data_file = scripts_path / '_xl-models-data.py'
TRINITY_VERSION = "1.1.0"
CONFIG_PATH = PROJECT_ROOT / "trinity_config.json"
LOG_FILE = PROJECT_ROOT / "trinity_unified.log"

def log_to_unified(message, level="INFO", component="CONFIG-HUB"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [v{TRINITY_VERSION}] [{level}] [{component}] {message}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f: f.write(log_entry)
    except: pass

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

def save_config(webui_choice, sd_version, models, vaes, controlnets, loras, arguments, theme_accent, civitai_token, ngrok_token, tunnel_choice):
    session_id = f"TR_{int(time.time())}"
    config_data = {
        "webui_choice": webui_choice, "sd_version": "SDXL" if sd_version else "SD1.5",
        "selected_models": models, "selected_vaes": vaes,
        "selected_controlnets": controlnets, "selected_loras": loras,
        "custom_args": arguments, "theme": theme_accent, "civitai_token": civitai_token,
        "ngrok_token": ngrok_token, "tunnel_choice": tunnel_choice, "session_id": session_id,
    }
    try:
        with open(CONFIG_PATH, "w", encoding='utf-8') as f: json.dump(config_data, f, indent=4)
        success_msg = f"✅ Config saved for {webui_choice}. You can now run the next cells."
        log_to_unified(success_msg, "SUCCESS")
        return gr.update(value=success_msg)
    except Exception as e:
        error_msg = f"❌ Failed to save config: {e}"
        log_to_unified(error_msg, "ERROR")
        return gr.update(value=error_msg)

def create_trinity_interface():
    with gr.Blocks(theme=gr.themes.Base()) as interface:
        gr.Markdown(f"# 🚀 Trinity Configuration Hub v{TRINITY_VERSION}")
        with gr.Row():
            webui_dropdown = gr.Dropdown(list(webui_selection.keys()), label="Select WebUI", value="A1111")
            is_xl_checkbox = gr.Checkbox(label="Use SDXL Models", value=False)
            tunnel_choice = gr.Radio(["Gradio", "ngrok"], label="Tunneling Service", value="Gradio")
        with gr.Accordion("Model Selection", open=True):
            model_cbg = gr.CheckboxGroup([], label="Checkpoint Model(s)")
            vae_cbg = gr.CheckboxGroup([], label="VAE(s)")
            controlnet_cbg = gr.CheckboxGroup([], label="ControlNet(s)")
            lora_cbg = gr.CheckboxGroup([], label="LoRA(s)")
        with gr.Accordion("Advanced & Secrets", open=False):
            arguments_textbox = gr.Textbox(label="Custom Launch Arguments", lines=1)
            theme_dropdown = gr.Dropdown(["Default", "Dark", "Light"], label="Theme", value="Default")
            civitai_token = gr.Textbox(label="Civitai API Token", type="password")
            ngrok_token = gr.Textbox(label="Ngrok Token", type="password")
        save_button = gr.Button("💾 Save Configuration", variant="primary")
        status_display = gr.Markdown("Ready.")
        
        is_xl_checkbox.change(fn=update_model_lists_for_version, inputs=is_xl_checkbox, outputs=[model_cbg, vae_cbg, controlnet_cbg, lora_cbg])
        webui_dropdown.change(fn=lambda w: gr.update(value=webui_selection.get(w,"")), inputs=webui_dropdown, outputs=arguments_textbox)
        save_button.click(fn=save_config,
            inputs=[webui_dropdown, is_xl_checkbox, model_cbg, vae_cbg, controlnet_cbg, lora_cbg, arguments_textbox, theme_dropdown, civitai_token, ngrok_token, tunnel_choice],
            outputs=[status_display]
        )
        interface.load(fn=lambda: update_model_lists_for_version(False), outputs=[model_cbg, vae_cbg, controlnet_cbg, lora_cbg])
    return interface

def launch_trinity_configuration_hub():
    try:
        log_to_unified("Initializing Config Hub...")
        interface = create_trinity_interface()
        port = int(os.environ.get('TRINITY_CONFIG_PORT', 7860))
        
        # --- THIS IS THE CRITICAL FIX ---
        # Added share=True to generate the public link
        interface.launch(
            server_name="0.0.0.0", 
            server_port=port, 
            share=True, # <-- THIS IS THE FIX
            quiet=False, 
            show_error=True, 
            inline=False
        )
        
    except Exception as e:
        log_to_unified(f"Failed to launch Config Hub: {e}", "ERROR")

if __name__ == "__main__":
    launch_trinity_configuration_hub()

