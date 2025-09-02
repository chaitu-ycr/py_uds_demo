from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_uds_demo.core.server import UdsServer
from py_uds_demo.core.utils.helpers import split_integer_to_bytes


class ReadDataByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # 0x13: IncorrectMessageLengthOrInvalidFormat
        if len(data_stream) != 3:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RDBI, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        did = (data_stream[1] << 8) | data_stream[2]
        match did:
            case self.uds_server.did.ACTIVE_DIAGNOSTIC_SESSION:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + [self.uds_server.diagnostic_session_control.active_session])
            case self.uds_server.did.VEHICLE_IDENTIFICATION_NUMBER:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.vehicle_identification_number)
            case self.uds_server.did.MANUFACTURER_SPARE_PART_NUMBER:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.manufacturer_spare_part_number)
            case self.uds_server.did.MANUFACTURER_ECU_SOFTWARE_NUMBER:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.manufacturer_ecu_software_number)
            case self.uds_server.did.MANUFACTURER_ECU_SOFTWARE_VERSION:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.manufacturer_ecu_software_version)
            case self.uds_server.did.ECU_MANUFACTURING_DATE:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.ecu_manufacturing_date)
            case self.uds_server.did.ECU_SERIAL_NUMBER:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.ecu_serial_number)
            case self.uds_server.did.SUPPORTED_FUNCTIONAL_UNITS:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.supported_functional_units)
            case self.uds_server.did.SYSTEM_SUPPLIER_ECU_SOFTWARE_NUMBER:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.system_supplier_ecu_software_number)
            case self.uds_server.did.SYSTEM_SUPPLIER_ECU_SOFTWARE_VERSION:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.system_supplier_ecu_software_version)
            case self.uds_server.did.PROGRAMMING_DATE:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.programming_date)
            case self.uds_server.did.REPAIR_SHOP_CODE:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.repair_shop_code)
            case self.uds_server.did.EXHAUST_REGULATION_TYPE_APPROVAL_NUMBER:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.exhaust_regulation_type_approval_number)
            case self.uds_server.did.INSTALLATION_DATE:
                return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RDBI, data_stream[1:3] + self.uds_server.memory.ecu_installation_date)
            case _:
                return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RDBI, self.uds_server.NRC.REQUEST_OUT_OF_RANGE)


class ReadMemoryByAddress:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if len(data_stream) != 5:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RMBA, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        address = (data_stream[1] << 24) | (data_stream[2] << 16) | (data_stream[3] << 8) | data_stream[4]

        if address not in self.uds_server.memory.memory_map:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RMBA, self.uds_server.NRC.REQUEST_OUT_OF_RANGE)

        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.RMBA, self.uds_server.memory.memory_map[address])


class ReadScalingDataByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RSDBI, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)


class ReadDataByPeriodicIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.RDBPI, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)


class DynamicallyDefineDataIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This service is not fully implemented in this simulator
        return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.DDDI, self.uds_server.NRC.SERVICE_NOT_SUPPORTED)


class WriteDataByIdentifier:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if len(data_stream) < 4:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.WDBI, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        did = (data_stream[1] << 8) | data_stream[2]

        if did not in self.uds_server.memory.writable_dids:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.WDBI, self.uds_server.NRC.REQUEST_OUT_OF_RANGE)

        data_to_write = data_stream[3:]

        # Simulate writing to a DID
        # In a real ECU, this would update a value in memory
        self.uds_server.memory.did_data[did] = data_to_write

        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.WDBI, data_stream[1:3])


class WriteMemoryByAddress:
    def __init__(self, uds_server: 'UdsServer') -> None:
        self.uds_server: 'UdsServer' = uds_server

    def process_request(self, data_stream: list) -> list:
        # This is a simulated implementation
        if len(data_stream) < 6:
            return self.uds_server.negative_response.report_negative_response(self.uds_server.SID.WMBA, self.uds_server.NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        address = (data_stream[1] << 24) | (data_stream[2] << 16) | (data_stream[3] << 8) | data_stream[4]
        data_to_write = data_stream[5:]

        # Simulate writing to memory
        self.uds_server.memory.memory_map[address] = data_to_write

        return self.uds_server.positive_response.report_positive_response(self.uds_server.SID.WMBA, [])
