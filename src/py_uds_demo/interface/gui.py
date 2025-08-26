import customtkinter as ctk

from py_uds_demo.core.client import UdsClient


class Gui:
    def __init__(self):
        self.client = UdsClient()
        self.root = ctk.CTk()
        self.root.title("🛠️ UDS Simulation GUI")
        self.root.geometry("920x500")

    def run(self):
        self._create_ui()
        self.root.mainloop()

    def _create_ui(self):
        options_frame = ctk.CTkFrame(self.root, border_color="grey", border_width=2)
        options_frame.pack(padx=5, pady=5, fill=ctk.X)
        self.tester_present_checkbox = ctk.CTkCheckBox(options_frame, text="Tester Present", command=self._toggle_tester_present)
        self.tester_present_checkbox.pack(padx=5, pady=5, anchor=ctk.NE)
        request_response_frame = ctk.CTkFrame(self.root, border_color="orange", border_width=2)
        request_response_frame.pack(padx=5, pady=5, fill=ctk.BOTH, expand=True)
        request_frame = ctk.CTkFrame(request_response_frame)
        request_frame.pack(padx=5, pady=5, fill=ctk.BOTH, expand=True)
        request_label = ctk.CTkLabel(request_frame, text="📥 Tx")
        request_label.pack(side=ctk.LEFT, padx=5, pady=5)
        self.request_entry = ctk.CTkEntry(request_frame)
        self.request_entry.pack(side=ctk.LEFT, padx=5, pady=5, fill=ctk.X, expand=True)
        self.request_entry.bind("<Return>", lambda event: self._send_request_callback())
        send_button = ctk.CTkButton(request_frame, text="Send", command=self._send_request_callback)
        send_button.pack(side=ctk.LEFT, padx=5, pady=5)
        response_frame = ctk.CTkFrame(request_response_frame)
        response_frame.pack(padx=5, pady=5, fill=ctk.BOTH, expand=True)
        response_label = ctk.CTkLabel(response_frame, text="📤 Rx")
        response_label.pack(side=ctk.LEFT, padx=5, pady=5)
        self.response_textbox = ctk.CTkTextbox(response_frame, height=50)
        self.response_textbox.pack(padx=5, pady=5, fill=ctk.BOTH, expand=True)
        history_frame = ctk.CTkFrame(self.root, border_color="green", border_width=2)
        history_frame.pack(padx=5, pady=5, fill=ctk.BOTH, expand=True)
        history_label = ctk.CTkLabel(history_frame, text=" 📃 History")
        history_label.pack(pady=5)
        self.history_textbox = ctk.CTkTextbox(history_frame)
        self.history_textbox.pack(padx=5, pady=5, fill=ctk.BOTH, expand=True)

    def _send_request_callback(self):
        request_data: str = self.request_entry.get()
        request_data_formatted = ""
        response_data_formatted = ""
        try:
            request_data = request_data.replace(" ", "")
            request_data_stream: list = [int(request_data[i:i+2], 16) for i in range(0, len(request_data), 2)]
            request_data_formatted = " ".join(f"{b:02X}" for b in request_data_stream)
            response_data = self.client.send_request(request_data_stream, False)
            response_data_formatted = " ".join(f"{b:02X}" for b in response_data)
        except ValueError:
            request_data_formatted = f"😡 Invalid input({request_data}). Please enter a valid hex string."
        except Exception as e:
            request_data_formatted = f"😡 An error occurred: {e}"
        finally:
            self.response_textbox.delete(1.0, ctk.END)
            self.response_textbox.insert(ctk.END, response_data_formatted)
            current_history = self.history_textbox.get(1.0, ctk.END)
            new_entry = f"-> {request_data_formatted}\n<- {response_data_formatted}\n"
            self.history_textbox.delete(1.0, ctk.END)
            self.history_textbox.insert(1.0, new_entry + current_history)

    def _toggle_tester_present(self):
        if self.tester_present_checkbox.get():
            self.client.server.diagnostic_session_control.tester_present_active = True
        else:
            self.client.server.diagnostic_session_control.tester_present_active = False


if __name__ == "__main__":
    gui = Gui()
    gui.run()
