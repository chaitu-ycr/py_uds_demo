from typing import Union
from py_uds_demo.core.server import UdsServer


class UdsClient:
    """Client for sending UDS requests and formatting responses.

    This class interfaces with the UdsServer to send diagnostic requests and process responses.
    """
    def __init__(self):
        """Initializes the UdsClient and creates an instance of UdsServer."""
        self.server = UdsServer()

    def _format_request(self, request: list) -> str:
        """Formats the UDS request as a string.

        Args:
            request (list): The request bytes to format.

        Returns:
            str: Formatted request string.
        """
        return "💉 " + " ".join(f"{byte:02X}" for byte in request)

    def _format_response(self, response: list) -> str:
        """Formats the server response as a string with status indicator.

        Args:
            response (list): The response bytes from the server.

        Returns:
            str: Formatted response string with a status indicator (🟢 for positive, 🔴 for negative).
        """
        if response[0] == self.server.SID.NEGATIVE_RESPONSE:
            return "🔴 " + " ".join(f"{byte:02X}" for byte in response)
        else:
            return "🟢 " + " ".join(f"{byte:02X}" for byte in response)

    def send_request(self, data_stream: Union[list, list[int]], return_formatted_stream: bool) -> Union[list, str]:
        """Sends a UDS request to the server and returns the response.

        Args:
            data_stream (list or list[int]): The request data to send to the server.
            return_formatted_stream (bool): If True, returns a formatted string; otherwise, returns the raw response list.

        Returns:
            Union[list, str]: The server response as a list of bytes or a formatted string.
        """
        self.server.logger.info(self._format_request(data_stream))
        response = self.server.process_request(data_stream)
        formatted_response = self._format_response(response)
        self.server.logger.info(formatted_response)
        if return_formatted_stream:
            return formatted_response
        else:
            return response
