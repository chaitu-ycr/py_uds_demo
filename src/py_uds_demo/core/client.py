from typing import Union
from py_uds_demo.core.server import UdsServer


class UdsClient:
    def __init__(self):
        self.server = UdsServer()

    def _format_response(self, response: list) -> str:
        if response[0] == self.server.SID.NEGATIVE_RESPONSE:
            return "🔴 " + " ".join(f"{byte:02X}" for byte in response)
        else:
            return "🟢 " + " ".join(f"{byte:02X}" for byte in response)

    def send_request(self, data_stream: Union[list, list[int]], return_formatted_stream: bool) -> Union[list, str]:
        response = self.server.process_request(data_stream)
        if return_formatted_stream:
            return self._format_response(response)
        else:
            return response
