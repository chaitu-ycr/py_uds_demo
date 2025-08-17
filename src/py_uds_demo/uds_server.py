import time
import threading
from enum import Enum
from typing import Union


class UdsServer:
    def __init__(self):
        self.__active_session = self.sfid.default_session
        self.__tester_present_always_on_flag = False
        self.__elapsed_time = 0  # Elapsed time in seconds
        self.__timer = None
        self.__timer_lock = threading.Lock()
        self.__timer_cancelled = threading.Event()
        self.__start_session_timer()  # Start the timer when the class is initialized

    @property
    def ecu_data(self):
        return UdsServerData()

    @property
    def sid(self):
        return Sid()

    @property
    def sfid(self):
        return Sfid()

    @property
    def nrc(self):
        return Nrc()


    def process_request(self, request):
        if request[0] == self.sid.diagnostic_session_control:
            return self.diagnostic_session_control(request[1])
        return [self.sid.NR, request[0], 0x11]

    # Diagnostic and communication management
    def diagnostic_session_control(self, diagnostic_session_type: int):
        """service is used to enable different diagnostic sessions in the server(s).
        Check ISO 14229 doc for more information about service.

        Args:
            diagnostic_session_type (int): 1 byte parameter is used by the service to select the specific behavior of the server

        Returns:
            list: response (positive or negative) to the request
        """
        if (self.__active_session == self.sfid.programming_session and diagnostic_session_type == self.sfid.extended_session) or \
           (self.__active_session == self.sfid.default_session and diagnostic_session_type == self.sfid.programming_session):
            return [self.sid.NR, self.sid.DSC, self.nrc.sub_function_not_supported_in_active_session]
        elif diagnostic_session_type not in self.ecu_data.supported_diagnostic_session_types:
            return [self.sid.NR, self.sid.DSC, self.nrc.sub_function_not_supported]
        else:
            self.__active_session = diagnostic_session_type
            self.__elapsed_time = 0  # Reset elapsed time on session change
            return [self.sid.DSC + self.ecu_data.PRP, self.__active_session] + [0xFF] * 6

    def ecu_reset(self, reset_type: int) -> list[int]:
        """The ECUReset service is used by the client to request a server reset.
        Check ISO 14229 doc for more information about service.

        Args:
            reset_type (int): 1 byte parameter is used by the service to describe how the server has to perform the reset.

        Returns:
            list: response (positive or negative) to the request
        """
        return [self.sid.ER + self.ecu_data.PRP, reset_type]

    def security_access(self, security_access_type: int, security_access_data_record: list[int] = None) -> list[int]:
        """this service provide a means to access data and/or diagnostic services, which have restricted access for security, emissions, or safety reasons.
        Check ISO 14229 doc for more information about service.

        Args:
            security_access_type (int): 1 byte parameter indicates to the server the step in progress for this service, the level of security the client wants to access.
            security_access_data_record (list[int], optional): parameter is user optional to transmit data to a server when requesting the seed information. Defaults to None.

        Returns:
            list: response (positive or negative) to the request
        """
        response = [self.sid.SA + self.ecu_data.PRP]
        return response

    def communication_control(self, control_type: int, communication_type: int, node_identification_number: int = None) -> list[int]:
        """service used to switch on/off the transmission and/or the reception of certain messages.
        Check ISO 14229 doc for more information about service.

        Args:
            control_type (int): 1 byte parameter contains information on how the server shall modify the communication type.
            communication_type (int): 1 byte parameter is used to reference the kind of communication to be controlled.
            node_identification_number (int, optional): 2 byte parameter is used to identify a node on a sub-network somewhere in the vehicle. Defaults to None.

        Returns:
            list: response (positive or negative) to the request
        """
        response = [self.sid.CC + self.ecu_data.PRP]
        return response

    def tester_present(self, zero_sub_functions: int) -> list[int]:
        """This service is used to indicate to a server (or servers) that a client is still connected to the vehicle and that
        certain diagnostic services and/or communication that have been previously activated are to remain active.
        Check ISO 14229 doc for more information about service.

        Args:
            zero_sub_functions (int): 1 byte parameter is used to indicate that no sub-function beside the suppressPosRspMsgIndicationBit is supported by this service.

        Returns:
            list: response (positive or negative) to the request
        """
        self.__elapsed_time = 0
        return [self.sid.TP + self.ecu_data.PRP,]

    def access_timing_parameter(self, timing_parameter_access_type: int, timing_parameter_request_record: list[int] = None) -> list[int]:
        """service is used to read and change the default timing parameters of a communication link for the duration this communication link is active.
        Check ISO 14229 doc for more information about service.

        Args:
            timing_parameter_access_type (int): 1 byte parameter is used by the service to select the specific behavior of the server.
            timing_parameter_request_record (Nlist[int], optional): parameter record contains the timing parameter values to be set in the server. Defaults to None.

        Returns:
            list: response (positive or negative) to the request.
        """
        response = [self.sid.ATP + self.ecu_data.PRP]
        return response

    def secured_data_transmission(self, security_data_request_record: list[int]) -> list[int]:
        """service to transmit data that is protected against attacks from third parties - which could endanger data security.
        Check ISO 14229 doc for more information about service.

        Args:
            security_data_request_record (list[int]): parameter contains the data as processed by the Security Sub-Layer.

        Returns:
            list: response (positive or negative) to the request.
        """
        response = [self.sid.SDT + self.ecu_data.PRP]
        return response

    def control_dtc_setting(self, dtc_setting_type: int, dtc_setting_control_option_record: list[int] = None) -> list[int]:
        """service used by a client to stop or resume the updating of DTC status bits in the server.
        Check ISO 14229 doc for more information about service.

        Args:
            dtc_setting_type (int): 1 byte parameter used by the service to indicate to the server(s) whether diagnostic trouble code status bit updating shall stop or start again.
            dtc_setting_control_option_record (list[int], optional): parameter record is user optional to transmit data to a server when controlling the updating of DTC status bits. Defaults to None.

        Returns:
            list: response (positive or negative) to the request.
        """
        response = [self.sid.CDTCS + self.ecu_data.PRP]
        return response

    def response_on_event(self, event_type: int, event_window_time: int, event_type_record: list[int] = None, service_to_respond_to_record: list[int] = None) -> list[int]:
        """service requests a server to start or stop transmission of responses on a specified event.
        Check ISO 14229 doc for more information about service.

        Args:
            event_type (int): 1 byte parameter is used by the service to specify the event to be configured in the server and to control the service set up.
            event_window_time (int): 1 byte parameter is used to specify a window for the event logic to be active in the server.
            event_type_record (list[int], optional): parameter record contains additional parameters for the specified eventType. Defaults to None.
            service_to_respond_to_record (list[int], optional): parameter record contains the service parameters of the service to be executed in the server each time the specified event defined in the eventTypeRecord occurs. Defaults to None.

        Returns:
            list: response (positive or negative) to the request.
        """
        response = [self.sid.ROE + self.ecu_data.PRP]
        return response

    def link_control(self, link_control_type: int, link_control_mode_identifier: int = None, link_record: int = None) -> list[int]:
        """service is used to control the communication between the client and the server in order to gain bus bandwidth for diagnostic purposes.
        Check ISO 14229 doc for more information about service.

        Args:
            link_control_type (int): 1 byte parameter is used by the service to describe the action to be performed in the server.
            link_control_mode_identifier (int, optional): This conditional 1 byte parameter references a fixed defined mode parameter. Defaults to None.
            link_record (int, optional): This conditional 3 byte parameter record contains a specific mode parameter in case the sub-function parameter indicates that a specific parameter is used. Defaults to None.

        Returns:
            list: response (positive or negative) to the request.
        """
        response = [self.sid.LC + self.ecu_data.PRP]
        return response

    def __session_timer(self):
        check_interval = 0.05  # 50 milliseconds
        while not self.__timer_cancelled.is_set():
            time.sleep(check_interval)
            with self.__timer_lock:
                if self.__tester_present_always_on_flag:
                    self.__elapsed_time = 0
                    continue
                self.__elapsed_time += check_interval
                if self.__elapsed_time >= self.ecu_data.ecu_session_time and self.__active_session != self.sfid.default_session:
                    self.__active_session = self.sfid.default_session
                    self.__elapsed_time = 0
                    print("Session expired, back to default session 0x01")

    def __start_session_timer(self):
        with self.__timer_lock:
            if self.__timer is None or not self.__timer.is_alive():
                self.__timer_cancelled.clear()
                self.__timer = threading.Thread(target=self.__session_timer)
                self.__timer.daemon = True
                self.__timer.start()

    def __stop_session_timer(self):
        self.__timer_cancelled.set()
        if self.__timer is not None:
            self.__timer.join()


class UdsServerData:
    def __init__(self):
        # Diagnostic and communication management
        self.supported_diagnostic_session_types = {0x01, 0x02, 0x03}
        self.ecu_session_time = 5  # 5 seconds
        self.positive_response_padding = self.PRP = 0x40


class Sid(Enum):
    """This class holds all service identifiers name and its value respectively.
    Check ISO 14229 doc for more information.
    """
    def __init__(self) -> None:
        # Diagnostic and communication management
        self.diagnostic_session_control = self.DSC = 0x10

        self.ecu_reset = self.ER = 0x11
        self.security_access = self.SA = 0x27
        self.communication_control = self.CC = 0X28
        self.tester_present = self.TP = 0x3E
        self.access_timing_parameter = self.ATP = 0x83
        self.secured_data_transmission = self.SDT = 0x84
        self.control_dtc_setting = self.CDTCS = 0x85
        self.response_on_event = self.ROE = 0x86
        self.link_control = self.LC = 0x87
        # Data transmission
        self.read_data_by_identifier = self.RDBI = 0x22
        self.read_memory_by_address = self.RMBA = 0x23
        self.read_scaling_data_by_identifier = self.RSDBI = 0x24
        self.read_data_by_periodic_identifier = self.RDBPI = 0x2A
        self.dynamically_define_data_identifier = self.DDDI = 0x2C
        self.write_data_by_identifier = self.WDBI = 0x2E
        self.write_memory_by_address = self.WMBA = 0x3D
        # Stored data transmission
        self.clear_diagnostic_information = self.CDTCI = 0x14
        self.read_dtc_information = self.RDTCI = 0x19
        # Input Output control
        self.input_output_control_by_identifier = self.IOCBI = 0x2F
        # Remote activation of routine
        self.routine_control = self.RC = 0x31
        # Upload download
        self.request_download = self.RD = 0x34
        self.request_upload = self.RU = 0x35
        self.transfer_data = self.TD = 0x36
        self.request_transfer_exit = self.RTE = 0x37
        self.request_file_transfer = self.RFT = 0x38
        # Negative Response
        self.negative_response = self.NR = 0x7F


class Sfid(Enum):
    """This class holds all service identifier sub-functions name and its value respectively.
    Check ISO 14229 doc for more information.
    """
    def __init__(self) -> None:
        # diagnostic_session_control
        self.default_session = self.DS = 0x01
        self.programming_session = self.PRGS = 0x02
        self.extended_session = self.EXTDS = 0x03
        self.safety_system_diagnostic_session = self.SSDS = 0x04
        # ecu_reset
        self.hard_reset = self.HR = 0x01
        self.key_on_off_reset = self.KOFFONR = 0x02
        self.soft_reset = self.SR = 0x03
        self.enable_rapid_power_shutdown = self.ERPSD = 0x04
        self.disable_rapid_power_shutdown = self.DRPSD = 0x05
        # security_access
        self.request_seed = self.RSD = 0x01
        self.send_key = self.SK = 0x02
        # communication_control
        self.enable_rx_and_tx = self.ERXTX = 0x00
        self.enable_rx_and_disable_tx = self.ERXDTX = 0x01
        self.disable_rx_and_enable_tx = self.DRXETX = 0x02
        self.disable_rx_and_tx = self.DRXTX = 0x03
        self.enable_rx_and_disable_tx_with_enhanced_address_information = self.ERXDTXWEAI = 0x04
        self.enable_rx_and_tx_with_enhanced_address_information = self.ERXTXWEAI = 0x05
        # tester_present
        self.zero_sub_function = self.ZSUBF = 0x00
        # access_timing_parameter
        self.read_extended_timing_parameter_set = self.RETPS = 0x01
        self.set_timing_parameters_to_default_value = self.STPTDV = 0x02
        self.read_currently_active_timing_parameters = self.RCATP = 0x03
        self.set_timing_parameters_to_given_values = self.STPTGV = 0x04
        # control_dtc_setting
        self.on = self.ON = 0x01
        self.off = self.OFF = 0x02
        # response_on_event
        self.do_not_store_event = self.DNSE = 0x00
        self.store_event = self.SE = 0x01
        self.stop_response_on_event = self.STPROE = 0x00
        self.on_dtc_status_change = self.ONDTCS = 0x01
        self.on_timer_interrupt = self.OTI = 0x02
        self.on_change_of_data_identifier = self.OCODID = 0x03
        self.report_activated_events = self.RAE = 0x04
        self.start_response_on_event = self.STRTROE = 0x05
        self.clear_response_on_event = self.CLRROE = 0x06
        self.on_comparison_of_value = self.OCOV = 0x07
        # link_control
        self.verify_mode_transition_with_fixed_parameter = self.VMTWFP = 0x01
        self.verify_mode_transition_with_specific_parameter = self.VMTWSP = 0x02
        self.transition_mode = self.TM = 0x03
        # dynamically_define_data_identifier
        self.define_by_identifier = self.DBID = 0x01
        self.define_by_memory_address = self.DBMA = 0x02
        self.clear_dynamically_defined_data_identifier = self.CDDDID = 0x03
        # read_dtc_information
        self.report_number_of_dtc_by_status_mask = self.RNODTCBSM = 0x01
        self.report_dtc_by_status_mask = self.RDTCBSM = 0x02
        self.report_dtc_snapshot_identification = self.RDTCSSI = 0x03
        self.report_dtc_snapshot_record_by_dtc_number = self.RDTCSSBDTC = 0x04
        self.read_dtc_stored_data_by_record_number = self.RDTCSDBRN = 0x05
        self.report_dtc_ext_data_record_by_dtc_number = self.RDTCEDRBDN = 0x06
        self.report_number_of_dtc_by_severity_mask_record = self.RNODTCBSMR = 0x07
        self.report_dtc_by_severity_mask_record = self.RDTCBSMR = 0x08
        self.report_severity_information_of_dtc = self.RSIODTC = 0x09
        self.report_mirror_memory_dtc_ext_data_record_by_dtc_number = self.RMDEDRBDN = 0x10
        self.report_supported_dtc = self.RSUPDTC = 0x0A
        self.report_first_test_failed_dtc = self.RFTFDTC = 0x0B
        self.report_first_confirmed_dtc = self.RFCDTC = 0x0C
        self.report_most_recent_test_failed_dtc = self.RMRTFDTC = 0x0D
        self.report_most_recent_confirmed_dtc = self.RMRCDTC = 0x0E
        self.report_mirror_memory_dtc_by_status_mask = self.RMMDTCBSM = 0x0F
        self.report_number_of_mirror_memory_dtc_by_status_mask = self.RNOMMDTCBSM = 0x11
        self.report_number_of_emission_obd_dtc_by_status_mask = self.RNOOEBDDTCBSM = 0x12
        self.report_emission_obd_dtc_by_status_mask = self.ROBDDTCBSM = 0x13
        self.report_dtc_fault_detection_counter = self.RDTCFDC = 0x14
        self.report_dtc_with_permanent_status = self.RDTCWPS = 0x15
        self.report_dtc_ext_data_record_by_record_number = self.RDTCEDRBR = 0x16
        self.report_user_def_memory_dtc_by_status_mask = self.RUDMDTCBSM = 0x17
        self.report_user_def_memory_dtc_snapshot_record_by_dtc_number = self.RUDMDTCSSBDTC = 0x18
        self.report_user_def_memory_dtc_ext_data_record_by_dtc_number = self.RUDMDTCEDRBDN = 0x19
        self.report_wwh_obd_dtc_by_mask_record = self.ROBDDTCBMR = 0x42
        self.report_wwh_obd_dtc_with_permanent_status = self.RWWHOBDDTCWPS = 0x55
        self.start_routine = self.STR = 0x01
        self.stop_routine = self.STPR = 0x02
        self.request_routine_result = self.RRR = 0x03


class Nrc(Enum):
    """This class holds all negative response codes name and its values respectively.
    Check ISO 14229 doc for more information.
    """
    def __init__(self) -> None:
        self.general_reject = self.GR = 0x10
        self.service_not_supported = self.SNS = 0x11
        self.sub_function_not_supported = self.SFNS = 0x12
        self.incorrect_message_length_or_invalid_format = self.IMLOIF = 0x13
        self.response_too_long = self.RTL = 0x14
        self.busy_repeat_request = self.BRR = 0x21
        self.conditions_not_correct = self.CNC = 0x22
        self.request_sequence_error = self.RSE = 0x24
        self.no_response_from_subnet_component = self.NRFSC = 0x25
        self.failure_prevents_execution_of_requested_action = self.FPEORA = 0x26
        self.request_out_of_range = self.ROOR = 0x31
        self.security_access_denied = self.SAD = 0x33
        self.invalid_key = self.IK = 0x35
        self.exceeded_number_of_attempts = self.ENOA = 0x36
        self.required_time_delay_not_expired = self.RTDNE = 0x37
        self.upload_download_not_accepted = self.UDNA = 0x70
        self.transfer_data_suspended = self.TDS = 0x71
        self.general_programming_failure = self.GPF = 0x72
        self.wrong_block_sequence_counter = self.WBSC = 0x73
        self.request_correctly_received_response_pending = self.RCRRP = 0x78
        self.sub_function_not_supported_in_active_session = self.SFNSIAS = 0x7E
        self.service_not_supported_in_active_session = self.SNSIAS = 0x7F
        self.rpm_too_high = self.RPMTH = 0x81
        self.rpm_too_low = self.RPMTL = 0x82
        self.engine_is_running = self.EIR = 0x83
        self.engine_is_not_running = self.EINR = 0x84
        self.engine_run_time_too_low = self.ERTTL = 0x85
        self.temperature_too_high = self.TEMPTH = 0x86
        self.temperature_too_low = self.TEMPTL = 0x87
        self.vehicle_speed_too_high = self.VSTH = 0x88
        self.vehicle_speed_too_low = self.VSTL = 0x89
        self.throttle_or_pedal_too_high = self.TPTH = 0x8A
        self.throttle_or_pedal_too_low = self.TPTL = 0x8B
        self.transmission_range_not_in_neutral = self.TRNIN = 0x8C
        self.transmission_range_not_in_gear = self.TRNIG = 0x8D
        self.brake_switch_not_closed = self.BSNC = 0x8F
        self.shifter_lever_not_in_park = self.SLNIP = 0x90
        self.torque_converter_clutch_locked = self.TCCL = 0x91
        self.voltage_too_high = self.VTH = 0x92
        self.voltage_too_low = self.VTL = 0x93
