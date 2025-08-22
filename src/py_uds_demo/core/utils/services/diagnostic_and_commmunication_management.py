import threading
import datetime
from time import sleep
from random import randint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer


class DiagnosticSessionControl:
    def __init__(self, uds_server: 'UdsServer'):
        self.uds_server: 'UdsServer' = uds_server
        self.active_session = self.uds_server.SFID.DEFAULT_SESSION
        self.tester_present_active = False
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
        if len(data_stream) != 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DSC, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        sfid = data_stream[1]
        if sfid not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DSC, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        self.active_session = sfid
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.DSC, [sfid, self.P2_HIGH, self.P2_LOW, self.P2_STAR_HIGH, self.P2_STAR_LOW])

    def start_active_session_timeout_thread(self):
        previous_time = int(datetime.datetime.now().timestamp())
        five_seconds = 5
        while True and not self.tester_present_active:
            current_time = int(datetime.datetime.now().timestamp())
            if current_time - previous_time > five_seconds:
                self.active_session = self.uds_server.SFID.DEFAULT_SESSION
                break
            else:
                sleep(0.1)


class EcuReset:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.supported_subfunctions = [
            self.uds_server.SFID.HARD_RESET,
            self.uds_server.SFID.KEY_ON_OFF_RESET,
            self.uds_server.SFID.SOFT_RESET,
        ]

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.ER, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        reset_type = data_stream[1]
        # 0x12: SubFunctionNotSupported
        if reset_type not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.ER, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        # 0x31: RequestOutOfRange (example: if reset_type is a valid subfunction but not allowed in current state)
        # HARD_RESET is allowed in programming session
        if (self.uds_server.diagnostic_session_control.active_session == self.uds_server.SFID.PROGRAMMING_SESSION and reset_type != self.uds_server.SFID.HARD_RESET):
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.ER, self.uds_server.NRC.REQUEST_OUT_OF_RANGE)
        self.uds_server.diagnostic_session_control.active_session = self.uds_server.SFID.DEFAULT_SESSION
        self.uds_server.security_access.seed_sent = False
        self.uds_server.security_access.security_unlock_success = False
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.ER, [reset_type])


class SecurityAccess:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.seed_value = []
        self.seed_sent = False
        self.security_unlock_success = False
        self.supported_subfunctions = [
            self.uds_server.SFID.REQUEST_SEED,
            self.uds_server.SFID.SEND_KEY,
        ]
        self.supported_sessions = [
            self.uds_server.SFID.PROGRAMMING_SESSION,
            self.uds_server.SFID.EXTENDED_SESSION,
        ]

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) < 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        # 0x22: ConditionsNotCorrect
        if self.uds_server.diagnostic_session_control.active_session not in self.supported_sessions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.CONDITIONS_NOT_CORRECT)
        sfid = data_stream[1]
        # 0x12: SubFunctionNotSupported
        if sfid not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        # 0x24: RequestSequenceError
        # - If a seed is requested when already sent, or key is sent before seed, or already unlocked
        if (sfid % 2 == 0 and not self.seed_sent) or (sfid % 2 == 1 and self.seed_sent) or self.security_unlock_success:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.REQUEST_SEQUENCE_ERROR)
        # Seed
        if sfid % 2 == 1:
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.SA, [sfid] + self._get_seed())
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 6:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        # Key
        if self._check_key(data_stream[2:]):
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.SA, [sfid])
        else:
            # 0x33: SecurityAccessDenied
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.SECURITY_ACCESS_DENIED)

    def _get_seed(self) -> list:
        self.seed_value = [randint(0, 255) for _ in range(4)]
        self.seed_sent = True
        return self.seed_value

    def _check_key(self, key: list) -> bool:
        internal_key = (
            (self.seed_value[0] << 24)
            | (self.seed_value[1] << 16)
            | (self.seed_value[2] << 8)
            | self.seed_value[3]
        ) | 0x11223344
        received_key = (
            (key[0] << 24)
            | (key[1] << 16)
            | (key[2] << 8)
            | key[3]
        )
        if internal_key == received_key:
            self.security_unlock_success = True
            return True
        return False


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
