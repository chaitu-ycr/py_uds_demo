from py_uds_demo.core.client import UdsClient


class Cli:
    def __init__(self):
        self.client = UdsClient()

    def _help(self):
        print("💡 Displaying help information.")
        print("💡 UDS CLI Help:")
        print("💡   Enter diagnostic requests in hex format (e.g., 22 F1 87).")
        print("💡   Type 'exit' or 'q' to quit the CLI.")
        print("💡   Type 'help' or 'h' or '?' for help.")

    def run(self):
        print("🏃‍➡️ Running UDS Simulation in CLI mode.")
        self._help()
        while True:
            user_input = input("💉 ")
            if user_input.lower() in ['exit', 'q']:
                print("👋 Closed UDS Simulation CLI mode.")
                break
            if user_input.lower() in ['help', 'h', '?']:
                self._help()
                continue
            diagnostic_request_clean = user_input.replace(" ", "")
            try:
                diagnostic_request_stream = [int(diagnostic_request_clean[i:i+2], 16) for i in range(0, len(diagnostic_request_clean), 2)]
                response = self.client.send_request(diagnostic_request_stream, True)
                print(response)
            except ValueError:
                print(f"😡 Invalid input({user_input}). Please enter a valid hex string.")
                continue


if __name__ == "__main__":
    cli = Cli()
    cli.run()
