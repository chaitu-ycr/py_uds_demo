from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class ReadDataByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, [0x00])


class ReadMemoryByAddress:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RMBA, [0x00])


class ReadScalingDataByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RSDBI, [0x00])


class ReadDataByPeriodicIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBPI, [0x00])


class DynamicallyDefineDataIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.DDDI, [0x00])


class WriteDataByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.WDBI, [0x00])


class WriteMemoryByAddress:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.WMBA, [0x00])
