import streamlit as st
from py_uds_demo.uds_client import UdsClient
from py_uds_demo.uds_server import UdsServer

class UdsApp:
    def __init__(self):
        if 'server' not in st.session_state:
            st.session_state.server = UdsServer()
        if 'client' not in st.session_state:
            st.session_state.client = UdsClient(st.session_state.server)
        if 'history' not in st.session_state:
            st.session_state.history = []  # Initialize history in session state

    def main(self):
        st.set_page_config(layout="wide")
        st.title("🕺⚽ UDS Protocol Playground")
        left_side_column, right_side_column = st.columns([7, 3])

        self.handle_left_side(left_side_column)
        self.handle_right_side(right_side_column)

    def handle_left_side(self, column):
        with column:
            self.uds_request = st.text_input("🚀 DIAGNOSTIC REQUEST")

            if self.uds_request:
                uds_response = st.session_state.client.send_request(self.uds_request)
                st.success(f"↩️🟰 {uds_response}")
                st.session_state.history.append({self.uds_request: uds_response})  # Append to history in session state
            else:
                st.error("please enter a request 👆 [recomended format 👉 10 02]")

            st.divider()
            self.display_history()

    def handle_right_side(self, column):
        with column:
            st.header("Helpful Information")
            if self.uds_request:
                st.info(f"Help info for: {self.uds_request}")
            else:
                st.info("Enter a request to get help information.")

    def display_history(self):
        st.header("📜 History")
        st.write(*reversed(st.session_state.history))
        # for req, res in reversed(st.session_state.history):
        #     st.write(f"""
        #              ➡️🟰 {req}

        #              ↩️🟰 {res}
        #              """)
        #     st.write("---")

if __name__ == "__main__":
    app = UdsApp()
    app.main()
