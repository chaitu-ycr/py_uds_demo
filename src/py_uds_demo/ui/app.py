import os
import logging
import gradio as gr

from py_uds_demo.core.client import UdsClient


class WebUi:
    def __init__(self):
        self.uds_client = UdsClient()
        self.tester_present_thread = None
        self.DEFAULT_LOG_FILE = "_temp/logs/uds_simulator.log"

    def run(self):
        """Launch the Gradio app."""
        self._initialize_logger()
        uds_sim = gr.Blocks()
        with uds_sim:
            self.uds_simulator_ui()
        uds_sim.launch()

    def uds_simulator_ui(self):
        """Build the Gradio UI for the UDS simulator."""
        self.tester_present_checkbox = gr.Checkbox(label="tester_present", value=False)
        self.uds_sim_chatbot = gr.Chatbot(type="messages", label="UDS Simulator(Chat Box)", show_label=True, show_copy_all_button=True, layout="bubble", value=[])
        self.diag_req_textbox = gr.Textbox(label="Diagnostic Request", placeholder="Enter diagnostic request in hex format (e.g., 22 F1)", show_label=True)
        self.diag_req_textbox.submit(self.chat_bot_process, [self.diag_req_textbox, self.uds_sim_chatbot], [self.diag_req_textbox, self.uds_sim_chatbot])
        self.tester_present_checkbox.change(self._set_tester_present, [self.tester_present_checkbox])

    def chat_bot_process(self, diagnostic_request, chat_history):
        """Process user diagnostic request and update chat history."""
        diagnostic_request_clean = diagnostic_request.replace(" ", "")
        try:
            diagnostic_request_stream = [int(diagnostic_request_clean[i:i+2], 16) for i in range(0, len(diagnostic_request_clean), 2)]
            user_sent_request = "💉 " + " ".join(f"{byte:02X}" for byte in diagnostic_request_stream)
            chat_history.append({"role": "user", "content": user_sent_request})
            self.logger.info(user_sent_request)
            diagnostic_response = self.uds_client.send_request(diagnostic_request_stream, True)
            chat_history.append({"role": "assistant", "content": diagnostic_response})
            self.logger.info(diagnostic_response)
        except ValueError:
            chat_history.append({"role": "user", "content": diagnostic_request})
            chat_history.append({"role": "assistant", "content": "Invalid hex input. Please enter a valid hex string."})
            self.logger.warning(f"Invalid Diagnostic Request 💉 {diagnostic_request}")
        except Exception as e:
            chat_history.append({"role": "user", "content": diagnostic_request})
            chat_history.append({"role": "assistant", "content": f"An error occurred while processing the request. {e}"})
            self.logger.error(f"Error occurred while processing request 💉 {diagnostic_request}: {e}")
        finally:
            return "", chat_history

    def _set_tester_present(self, value: bool):
        self.uds_client.server.diagnostic_session_control.tester_present_active = value
        self.logger.info('tester present [✔️] activated' if value else 'tester present [✖️] deactivated')

    def _initialize_logger(self):
        os.makedirs(os.path.dirname(self.DEFAULT_LOG_FILE), exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(self.DEFAULT_LOG_FILE) for h in self.logger.handlers):
            handler = logging.FileHandler(self.DEFAULT_LOG_FILE, encoding='utf-8')
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter("%(asctime)s [UDS_SIM_UI] [%(levelname)-4.8s] %(message)s"))
            self.logger.addHandler(handler)


if __name__ == "__main__":
    web_ui = WebUi()
    web_ui.run()
