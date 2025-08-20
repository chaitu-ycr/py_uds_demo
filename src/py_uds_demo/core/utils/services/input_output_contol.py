from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class InputOutputControlByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.IOCBI, [0x00])
