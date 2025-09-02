from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class InputOutputControlByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.io_control_status = {}

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if len(data_stream) < 4:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.IOCBI, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        did = (data_stream[1] << 8) | data_stream[2]
        control_option = data_stream[3]

        # In a real ECU, you would check if the DID is valid for I/O control
        # and if the control option is supported.

        self.io_control_status[did] = control_option

        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.IOCBI, data_stream[1:3])
