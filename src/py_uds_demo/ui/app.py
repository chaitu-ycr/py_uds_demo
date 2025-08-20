import gradio as gr
from py_uds_demo.core.client import UdsClient


class WebUi:
    def __init__(self):
        self.uds_client = UdsClient()

    def chat_bot_process(self, diagnostic_request, chat_history):
        diagnostic_request_clean = diagnostic_request.replace(" ", "")
        try:
            diagnostic_request_stream = [int(diagnostic_request_clean[i:i+2], 16) for i in range(0, len(diagnostic_request_clean), 2)]
            user_sent_request_formatted = "💉 " + " ".join(f"{byte:02X}" for byte in diagnostic_request_stream)
            chat_history.append({"role": "user", "content": user_sent_request_formatted})
            diagnostic_response = self.uds_client.send_request(diagnostic_request_stream, True)
            chat_history.append({"role": "assistant", "content": diagnostic_response})
        except ValueError:
            chat_history.append({"role": "user", "content": diagnostic_request})
            chat_history.append({"role": "assistant", "content": "Invalid hex input. Please enter a valid hex string."})
        except Exception as e:
            chat_history.append({"role": "user", "content": diagnostic_request})
            chat_history.append({"role": "assistant", "content": f"An error occurred while processing the request. {e}"})
        finally:
            return "", chat_history

    def uds_simulator_ui(self):
        chatbot = gr.Chatbot(type="messages", label="UDS Simulator(Chat Box)", show_label=True, show_copy_all_button=True, layout="bubble")
        msg = gr.Textbox(label="Diagnostic Request", placeholder="Enter diagnostic request in hex format (e.g., 22 F1)", show_label=True)
        msg.submit(self.chat_bot_process, [msg, chatbot], [msg, chatbot])

    def run(self):
        uds_sim = gr.Blocks()
        with uds_sim:
            self.uds_simulator_ui()
        uds_sim.launch()


if __name__ == "__main__":
    web_ui = WebUi()
    web_ui.run()
