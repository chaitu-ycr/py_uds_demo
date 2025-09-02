from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class RequestDownload:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RD, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)


class RequestUpload:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RU, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)

class TransferData:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.TD, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)


class RequestTransferExit:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RTE, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)


class RequestFileTransfer:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RFT, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)
