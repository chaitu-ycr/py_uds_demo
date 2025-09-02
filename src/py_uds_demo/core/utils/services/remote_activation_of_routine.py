from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class RoutineControl:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.routine_status = {}

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if len(data_stream) < 4:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RC, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        sub_function = data_stream[1]
        routine_id = (data_stream[2] << 8) | data_stream[3]

        if sub_function == self.uds_server.SFID.START_ROUTINE:
            # In a real ECU, you would start the routine
            self.routine_status[routine_id] = "Started"
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RC, data_stream[1:4])

        elif sub_function == self.uds_server.SFID.STOP_ROUTINE:
            # In a real ECU, you would stop the routine
            self.routine_status[routine_id] = "Stopped"
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RC, data_stream[1:4])

        elif sub_function == self.uds_server.SFID.REQUEST_ROUTINE_RESULT:
            # In a real ECU, you would get the result of the routine
            if routine_id in self.routine_status:
                # Returning a dummy result
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RC, data_stream[1:4] + [0x01, 0x02, 0x03])
            else:
                return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RC, self.uds_server.NRC.REQUEST_OUT_OF_RANGE)

        else:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RC, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
