from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class ClearDiagnosticInformation:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if self.uds_server.diagnostic_session_control.dtc_setting == self.uds_server.SFID.OFF:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CDTCI, self.uds_server.NRC.CONDITIONS_NOT_CORRECT)

        self.uds_server.memory.dtcs = []
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.CDTCI, [])


class ReadDtcInformation:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if len(data_stream) < 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RDTCI, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        sub_function = data_stream[1]

        if sub_function == self.uds_server.SFID.REPORT_NUMBER_OF_DTC_BY_STATUS_MASK:
            status_mask = data_stream[2]
            # In this simulation, we'll just count all DTCs regardless of status mask
            num_dtcs = len(self.uds_server.memory.dtcs)
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDTCI, [sub_function, status_mask, 0x01, num_dtcs])

        elif sub_function == self.uds_server.SFID.REPORT_DTC_BY_STATUS_MASK:
            status_mask = data_stream[2]
            # In this simulation, we'll return all DTCs regardless of status mask
            response_data = [sub_function, status_mask]
            for dtc in self.uds_server.memory.dtcs:
                response_data.extend(dtc)
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDTCI, response_data)

        else:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RDTCI, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
