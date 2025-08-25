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
        self.tester_present_active = False
        self.session_timeout = 5 # 5 seconds
        self.last_session_change_time = datetime.datetime.now()
        self.thread_event = threading.Event()
        self.session_thread = threading.Thread(target=self._start_active_session_timeout_thread, daemon=True)
        self.session_thread.start()

    def __del__(self):
        self.thread_event.set()
        self.session_thread.join(1)

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DSC, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        sfid = data_stream[1]
        # 0x12: SubFunctionNotSupported
        if sfid not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DSC, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        # Positive Response
        self.active_session = sfid
        self.last_session_change_time = datetime.datetime.now()
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.DSC, [sfid, self.P2_HIGH, self.P2_LOW, self.P2_STAR_HIGH, self.P2_STAR_LOW])

    def _start_active_session_timeout_thread(self):
        while not self.thread_event.is_set():
            if self.tester_present_active:
                sleep(0.1)
                continue
            now = datetime.datetime.now()
            elapsed = (now - self.last_session_change_time).total_seconds()
            if self.active_session != self.uds_server.SFID.DEFAULT_SESSION and elapsed >= self.session_timeout:
                self.active_session = self.uds_server.SFID.DEFAULT_SESSION
                self.last_session_change_time = now
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
        # Positive Response
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
        # Seed - Positive Response
        if sfid % 2 == 1:
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.SA, [sfid] + self._get_seed())
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 6:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.SA, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        # Key - Positive Response
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
        self.NORMAL_COMMUNICATION_MESSAGES = 0x01
        self.NETWORK_MANAGEMENT_MESSAGES = 0x01
        self.BOTH_TYPES = 0x01
        self.supported_subfunctions = [
            self.uds_server.SFID.ENABLE_RX_AND_TX,
            self.uds_server.SFID.ENABLE_RX_AND_DISABLE_TX,
            self.uds_server.SFID.DISABLE_RX_AND_ENABLE_TX,
            self.uds_server.SFID.DISABLE_RX_AND_TX,
        ]
        self.supported_communication_types = [
            self.NORMAL_COMMUNICATION_MESSAGES,
            self.NETWORK_MANAGEMENT_MESSAGES,
            self.BOTH_TYPES,
        ]
        self.supported_sessions = [
            self.uds_server.SFID.PROGRAMMING_SESSION,
            self.uds_server.SFID.EXTENDED_SESSION,
        ]

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if not (len(data_stream) >= 3):
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CC, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        # 0x22: ConditionsNotCorrect
        if self.uds_server.diagnostic_session_control.active_session not in self.supported_sessions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CC, self.uds_server.NRC.CONDITIONS_NOT_CORRECT)
        sfid = data_stream[1]
        # 0x12: SubFunctionNotSupported
        if sfid not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CC, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        # 0x31: Request out of range
        communication_type = data_stream[2]
        if communication_type not in self.supported_communication_types:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CC, self.uds_server.NRC.REQUEST_OUT_OF_RANGE)
        # Positive Response
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.CC, data_stream[1:])


class TesterPresent:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.tester_present_request_received = False
        self.supported_subfunctions = [
            self.uds_server.SFID.ZERO_SUB_FUNCTION,
            self.uds_server.SFID.ZERO_SUB_FUNCTION_SUPRESS_RESPONSE,
        ]

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.TP, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        # 0x12: SubFunctionNotSupported
        sfid = data_stream[1]
        if sfid not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.TP, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        # Positive Response
        self.tester_present_request_received = True
        if sfid == self.uds_server.SFID.ZERO_SUB_FUNCTION:
            return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.TP, data_stream[1:])
        else:
            return []  # Suppress response


class AccessTimingParameter:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.supported_subfunctions = [
            self.uds_server.SFID.READ_EXTENDED_TIMING_PARAMETER_SET,
            self.uds_server.SFID.SET_TIMING_PARAMETERS_TO_DEFAULT_VALUE,
            self.uds_server.SFID.READ_CURRENTLY_ACTIVE_TIMING_PARAMETERS,
            self.uds_server.SFID.SET_TIMING_PARAMETERS_TO_GIVEN_VALUES,
        ]

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.ATP, data_stream[1:])


class SecuredDataTransmission:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.SDT, data_stream[1:])


class ControlDtcSetting:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.supported_subfunctions = [
            self.uds_server.SFID.ON,
            self.uds_server.SFID.OFF,
        ]
        self.supported_sessions = [
            self.uds_server.SFID.PROGRAMMING_SESSION,
            self.uds_server.SFID.EXTENDED_SESSION,
        ]

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 2:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CDTCS, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        # 0x22: ConditionsNotCorrect
        if self.uds_server.diagnostic_session_control.active_session not in self.supported_sessions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CDTCS, self.uds_server.NRC.CONDITIONS_NOT_CORRECT)
        # 0x12: SubFunctionNotSupported
        sfid = data_stream[1]
        if sfid not in self.supported_subfunctions:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.CDTCS, self.uds_server.NRC.SUB_FUNCTION_NOT_SUPPORTED)
        # Positive Response
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.CDTCS, data_stream[1:])


class ResponseOnEvent:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.supported_subfunctions = [
            self.uds_server.SFID.DO_NOT_STORE_EVENT,
            self.uds_server.SFID.STORE_EVENT,
            self.uds_server.SFID.STOP_RESPONSE_ON_EVENT,
            self.uds_server.SFID.ON_DTC_STATUS_CHANGE,
            self.uds_server.SFID.ON_TIMER_INTERRUPT,
            self.uds_server.SFID.ON_CHANGE_OF_DATA_IDENTIFIER,
            self.uds_server.SFID.REPORT_ACTIVATED_EVENTS,
            self.uds_server.SFID.START_RESPONSE_ON_EVENT,
            self.uds_server.SFID.CLEAR_RESPONSE_ON_EVENT,
            self.uds_server.SFID.ON_COMPARISON_OF_VALUE,
        ]

    def process_request(self, data_stream: list) -> list:
        # Positive Response
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.ROE, data_stream[1:])


class LinkControl:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server
        self.supported_subfunctions = [
            self.uds_server.SFID.VERIFY_MODE_TRANSITION_WITH_FIXED_PARAMETER,
            self.uds_server.SFID.VERIFY_MODE_TRANSITION_WITH_SPECIFIC_PARAMETER,
            self.uds_server.SFID.TRANSITION_MODE,
        ]

    def process_request(self, data_stream: list) -> list:
        # Positive Response
        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.LC, data_stream[1:])
