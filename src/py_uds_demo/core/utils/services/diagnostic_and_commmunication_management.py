from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer

class DiagnosticSessionControl:
    def __init__(self, uds_server: 'UdsServer'):
        self.uds_server: 'UdsServer' = uds_server
        self.supported_subfunctions = [
            self.uds_server.SFID.DEFAULT_SESSION,
            self.uds_server.SFID.PROGRAMMING_SESSION,
            self.uds_server.SFID.EXTENDED_SESSION,
            self.uds_server.SFID.SAFETY_SYSTEM_DIAGNOSTIC_SESSION,
        ]
        # P2 = 50 ms
        self.P2_HIGH = 0x00
        self.P2_LOW = 0x32
        # P2* = 5000 ms
        self.P2_STAR_HIGH = 0x13
        self.P2_STAR_LOW = 0x88

    def process_request(self, data_stream: list) -> list:
        """Process the incoming data stream for diagnostic session control."""
        if len(data_stream) != 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DSC, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        sfid = data_stream[1]
        if not self.uds_server.negative_response.check_subfunction_supported(sfid, self.supported_subfunctions):
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DSC, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        self.uds_server.active_session = sfid
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.DSC, [sfid, self.P2_HIGH, self.P2_LOW, self.P2_STAR_HIGH, self.P2_STAR_LOW])


class EcuReset:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.ER, [0x00])


class SecurityAccess:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.SA, [0x00])


class CommunicationControl:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.CC, [0x00])


class TesterPresent:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.TP, [0x00])


class AccessTimingParameter:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.ATP, [0x00])


class SecuredDataTransmission:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.SDT, [0x00])


class ControlDtcSetting:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.CDTCS, [0x00])


class ResponseOnEvent:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.ROE, [0x00])


class LinkControl:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.LC, [0x00])
