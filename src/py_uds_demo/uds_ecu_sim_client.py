# UDS ECU Simulator Gradio Web Client
# Ultra-simple, professional automotive testing interface

import gradio as gr
import socket
import struct
import json
from datetime import datetime
import pandas as pd

class UDSClient:
    def __init__(self):
        self.history = []
        
    def send_request(self, host, port, request_bytes):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((host, int(port)))
                s.sendall(request_bytes)
                response = s.recv(4096)
            
            return {
                'success': True,
                'response': response.hex().upper(),
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'error': str(e)
            }
    
    def add_to_history(self, service_name, request_hex, response_hex, success, error=None):
        entry = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Service': service_name,
            'Request': request_hex,
            'Response': response_hex if success else f"ERROR: {error}",
            'Status': '✅ SUCCESS' if success else '❌ FAILED'
        }
        self.history.insert(0, entry)  # Add to beginning
        self.history = self.history[:50]  # Keep only last 50
        
        # Convert to DataFrame for nice display
        df = pd.DataFrame(self.history)
        return df

# Global client instance
client = UDSClient()

def build_uds_request(service_name, param1="", param2="", param3=""):
    """Build UDS request based on service and parameters"""
    
    service_map = {
        "Diagnostic Session Control (0x10)": 0x10,
        "ECU Reset (0x11)": 0x11,
        "Security Access (0x27)": 0x27,
        "Tester Present (0x3E)": 0x3E,
        "Read Data By Identifier (0x22)": 0x22,
        "Write Data By Identifier (0x2E)": 0x2E,
        "Clear Diagnostic Information (0x14)": 0x14,
        "Read DTC Information (0x19)": 0x19,
        "Control DTC Setting (0x85)": 0x85,
        "Routine Control (0x31)": 0x31
    }
    
    if service_name not in service_map:
        return None
    
    service_id = service_map[service_name]
    request_data = [service_id]
    
    try:
        if service_id == 0x10:  # Diagnostic Session Control
            session_types = {"Default": 0x01, "Programming": 0x02, "Extended": 0x03}
            session_type = session_types.get(param1, 0x01)
            request_data.append(session_type)
            
        elif service_id == 0x11:  # ECU Reset
            reset_types = {"Hard Reset": 0x01, "Key Off/On": 0x02, "Soft Reset": 0x03}
            reset_type = reset_types.get(param1, 0x01)
            request_data.append(reset_type)
            
        elif service_id == 0x27:  # Security Access
            sub_func = int(param1) if param1 else 1
            request_data.append(sub_func)
            
            # If even sub-function (send key), add key data
            if sub_func % 2 == 0 and param2:
                try:
                    key_bytes = bytes.fromhex(param2.replace(' ', ''))
                    request_data.extend(key_bytes)
                except ValueError:
                    pass
                    
        elif service_id == 0x3E:  # Tester Present
            request_data.append(0x00)
            
        elif service_id == 0x22:  # Read Data By Identifier
            dids_str = param1 if param1 else "F186"
            dids = [d.strip() for d in dids_str.replace(',', ' ').split()]
            for did_str in dids:
                did = int(did_str, 16)
                request_data.extend([(did >> 8) & 0xFF, did & 0xFF])
                
        elif service_id == 0x2E:  # Write Data By Identifier
            did_str = param1 if param1 else "F186"
            data_str = param2 if param2 else "NEW_VALUE"
            
            did = int(did_str, 16)
            request_data.extend([(did >> 8) & 0xFF, did & 0xFF])
            
            # Add data
            if ' ' in data_str and all(len(x) == 2 for x in data_str.split()):
                data_bytes = bytes.fromhex(data_str.replace(' ', ''))
            else:
                data_bytes = data_str.encode('utf-8')
            request_data.extend(data_bytes)
            
        elif service_id == 0x14:  # Clear Diagnostic Information
            group_str = param1 if param1 else "FFFFFF"
            group = int(group_str, 16)
            request_data.extend([(group >> 16) & 0xFF, (group >> 8) & 0xFF, group & 0xFF])
            
        elif service_id == 0x19:  # Read DTC Information
            sub_funcs = {"Report DTC By Status": 0x02, "Report Supported DTC": 0x0A}
            sub_func = sub_funcs.get(param1, 0x02)
            request_data.append(sub_func)
            
            if sub_func == 0x02 and param2:  # Status mask
                mask = int(param2, 16) if param2 else 0xFF
                request_data.append(mask)
            elif sub_func == 0x02:
                request_data.append(0xFF)  # Default status mask
                
        elif service_id == 0x85:  # Control DTC Setting
            dtc_settings = {"DTC Setting On": 0x01, "DTC Setting Off": 0x02}
            sub_func = dtc_settings.get(param1, 0x01)
            request_data.append(sub_func)
            
        elif service_id == 0x31:  # Routine Control
            routine_funcs = {"Start Routine": 0x01, "Stop Routine": 0x02, "Request Results": 0x03}
            sub_func = routine_funcs.get(param1, 0x01)
            routine_id_str = param2 if param2 else "1234"
            
            request_data.append(sub_func)
            routine_id = int(routine_id_str, 16)
            request_data.extend([(routine_id >> 8) & 0xFF, routine_id & 0xFF])
        
        return bytes(request_data)
        
    except Exception as e:
        print(f"Error building request: {e}")
        return None

def send_uds_request(host, port, service_name, param1, param2, param3):
    """Main function to send UDS request and return results"""
    
    # Build request
    request_bytes = build_uds_request(service_name, param1, param2, param3)
    if not request_bytes:
        error_msg = "Failed to build UDS request. Check parameters."
        df = client.add_to_history(service_name, "INVALID", error_msg, False, "Invalid parameters")
        return f"❌ {error_msg}", "", df
    
    request_hex = request_bytes.hex().upper()
    
    # Send request
    result = client.send_request(host, port, request_bytes)
    
    if result['success']:
        response_hex = result['response']
        df = client.add_to_history(service_name, request_hex, response_hex, True)
        status_msg = f"✅ Request sent successfully!"
        return status_msg, f"**Request:** {request_hex}\n**Response:** {response_hex}", df
    else:
        error_msg = result['error']
        df = client.add_to_history(service_name, request_hex, error_msg, False, error_msg)
        status_msg = f"❌ Connection failed: {error_msg}"
        return status_msg, f"**Request:** {request_hex}\n**Error:** {error_msg}", df

def clear_history():
    """Clear the request history"""
    client.history = []
    empty_df = pd.DataFrame(columns=['Timestamp', 'Service', 'Request', 'Response', 'Status'])
    return empty_df, "🗑️ History cleared!"

def get_parameter_info(service_name):
    """Return parameter information based on selected service"""
    
    param_info = {
        "Diagnostic Session Control (0x10)": {
            "param1": ("Session Type", "dropdown", ["Default", "Programming", "Extended"]),
            "param2": ("", "hidden", []),
            "param3": ("", "hidden", [])
        },
        "ECU Reset (0x11)": {
            "param1": ("Reset Type", "dropdown", ["Hard Reset", "Key Off/On", "Soft Reset"]),
            "param2": ("", "hidden", []),
            "param3": ("", "hidden", [])
        },
        "Security Access (0x27)": {
            "param1": ("Sub-Function", "text", "1 (odd=seed, even=key)"),
            "param2": ("Key (hex, for even sub-functions)", "text", "e.g., A1B2"),
            "param3": ("", "hidden", [])
        },
        "Tester Present (0x3E)": {
            "param1": ("", "hidden", []),
            "param2": ("", "hidden", []),
            "param3": ("", "hidden", [])
        },
        "Read Data By Identifier (0x22)": {
            "param1": ("DID(s) (hex, space/comma separated)", "text", "F186 F190"),
            "param2": ("", "hidden", []),
            "param3": ("", "hidden", [])
        },
        "Write Data By Identifier (0x2E)": {
            "param1": ("DID (hex)", "text", "F186"),
            "param2": ("Data (text or hex bytes)", "text", "NEW_VALUE"),
            "param3": ("", "hidden", [])
        },
        "Clear Diagnostic Information (0x14)": {
            "param1": ("Group of DTC (hex)", "text", "FFFFFF (all)"),
            "param2": ("", "hidden", []),
            "param3": ("", "hidden", [])
        },
        "Read DTC Information (0x19)": {
            "param1": ("Sub-Function", "dropdown", ["Report DTC By Status", "Report Supported DTC"]),
            "param2": ("Status Mask (hex)", "text", "FF"),
            "param3": ("", "hidden", [])
        },
        "Control DTC Setting (0x85)": {
            "param1": ("DTC Setting", "dropdown", ["DTC Setting On", "DTC Setting Off"]),
            "param2": ("", "hidden", []),
            "param3": ("", "hidden", [])
        },
        "Routine Control (0x31)": {
            "param1": ("Sub-Function", "dropdown", ["Start Routine", "Stop Routine", "Request Results"]),
            "param2": ("Routine ID (hex)", "text", "1234"),
            "param3": ("", "hidden", [])
        }
    }
    
    return param_info.get(service_name, {
        "param1": ("", "hidden", []),
        "param2": ("", "hidden", []),
        "param3": ("", "hidden", [])
    })

# Create Gradio interface
def create_interface():
    
    # Custom CSS for professional automotive look
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', system-ui, sans-serif !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
    .gr-button-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
    }
    .gr-button-secondary {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
        border: none !important;
        color: white !important;
    }
    h1 {
        color: #2c3e50 !important;
        text-align: center !important;
        margin-bottom: 1rem !important;
    }
    .gr-box {
        border-radius: 8px !important;
        border: 1px solid #e1e5e9 !important;
    }
    """
    
    with gr.Blocks(css=custom_css, title="UDS ECU Simulator", theme=gr.themes.Soft()) as demo:
        
        gr.HTML("<h1>🚗 UDS ECU Simulator Professional Tester</h1>")
        gr.Markdown("**Professional automotive diagnostic testing interface - Send UDS requests and monitor responses in real-time**")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🔌 Connection Settings")
                host_input = gr.Textbox(value="localhost", label="ECU Simulator Host", placeholder="localhost or IP address")
                port_input = gr.Number(value=6801, label="Port", precision=0)
                
                gr.Markdown("### 📡 UDS Service Request")
                service_dropdown = gr.Dropdown(
                    choices=[
                        "Diagnostic Session Control (0x10)",
                        "ECU Reset (0x11)", 
                        "Security Access (0x27)",
                        "Tester Present (0x3E)",
                        "Read Data By Identifier (0x22)",
                        "Write Data By Identifier (0x2E)",
                        "Clear Diagnostic Information (0x14)",
                        "Read DTC Information (0x19)",
                        "Control DTC Setting (0x85)",
                        "Routine Control (0x31)"
                    ],
                    value="Read Data By Identifier (0x22)",
                    label="Select UDS Service"
                )
                
                # Dynamic parameter inputs
                param1_input = gr.Textbox(label="DID(s) (hex, space/comma separated)", value="F186 F190", visible=True)
                param2_input = gr.Textbox(label="Parameter 2", visible=False)
                param3_input = gr.Textbox(label="Parameter 3", visible=False)
                
                # Buttons
                with gr.Row():
                    send_btn = gr.Button("🚀 Send UDS Request", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear History", variant="secondary")
                
                # Status display
                status_output = gr.Textbox(label="📊 Status", interactive=False, lines=1)
                
            with gr.Column(scale=2):
                gr.Markdown("### 📋 Request/Response History")
                
                # Current request/response display
                current_display = gr.Markdown("**No request sent yet**", label="Current Exchange")
                
                # History table
                history_table = gr.Dataframe(
                    headers=["Timestamp", "Service", "Request", "Response", "Status"],
                    datatype=["str", "str", "str", "str", "str"],
                    col_count=(5, "fixed"),
                    row_count=(10, "dynamic"),
                    wrap=True,
                    label="Communication History (Last 50 entries)"
                )
        
        # Dynamic parameter update based on service selection
        def update_parameters(service_name):
            info = get_parameter_info(service_name)
            
            # Update param1
            param1_info = info["param1"]
            if param1_info[1] == "dropdown":
                param1_visible = True
                param1_component = gr.update(
                    label=param1_info[0], 
                    visible=param1_visible,
                    value=param1_info[2][0] if param1_info[2] else ""
                )
            elif param1_info[1] == "text":
                param1_visible = True
                param1_component = gr.update(
                    label=param1_info[0], 
                    visible=param1_visible,
                    value=param1_info[2] if isinstance(param1_info[2], str) else "",
                    placeholder=param1_info[2] if isinstance(param1_info[2], str) else ""
                )
            else:
                param1_visible = False
                param1_component = gr.update(visible=param1_visible)
            
            # Update param2
            param2_info = info["param2"]
            if param2_info[1] == "text":
                param2_visible = True
                param2_component = gr.update(
                    label=param2_info[0], 
                    visible=param2_visible,
                    value=param2_info[2] if isinstance(param2_info[2], str) else "",
                    placeholder=param2_info[2] if isinstance(param2_info[2], str) else ""
                )
            else:
                param2_visible = False
                param2_component = gr.update(visible=param2_visible)
            
            # param3 is always hidden for now
            param3_component = gr.update(visible=False)
            
            return param1_component, param2_component, param3_component
        
        # Event handlers
        service_dropdown.change(
            fn=update_parameters,
            inputs=[service_dropdown],
            outputs=[param1_input, param2_input, param3_input]
        )
        
        send_btn.click(
            fn=send_uds_request,
            inputs=[host_input, port_input, service_dropdown, param1_input, param2_input, param3_input],
            outputs=[status_output, current_display, history_table]
        )
        
        clear_btn.click(
            fn=clear_history,
            outputs=[history_table, status_output]
        )
        
        # Initialize with default service
        demo.load(
            fn=update_parameters,
            inputs=[service_dropdown],
            outputs=[param1_input, param2_input, param3_input]
        )
    
    return demo

# Launch the application
if __name__ == "__main__":
    print("🚗 UDS ECU Simulator Gradio Client")
    print("=" * 50)
    print("✅ Starting professional automotive testing interface...")
    print("🔧 Make sure your UDS ECU Simulator is running on localhost:6801")
    print("🌐 Web interface will open automatically in your browser")
    print("📱 Share link will be generated for team collaboration")
    print("=" * 50)
    
    interface = create_interface()
    interface.launch(
        share=True,          # Creates shareable link
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,    # Standard Gradio port
        show_error=True,     # Show detailed errors
        inbrowser=True       # Auto-open browser
    )