import socket
import struct
import threading
import time
from enum import Enum
from typing import Dict, List, Optional, Callable

class UDSServices(Enum):
    """UDS Service Identifiers"""
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    ECU_RESET = 0x11
    SECURITY_ACCESS = 0x27
    COMMUNICATION_CONTROL = 0x28
    TESTER_PRESENT = 0x3E
    ACCESS_TIMING_PARAMETER = 0x83
    SECURED_DATA_TRANSMISSION = 0x84
    CONTROL_DTC_SETTING = 0x85
    RESPONSE_ON_EVENT = 0x86
    LINK_CONTROL = 0x87
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_MEMORY_BY_ADDRESS = 0x23
    READ_SCALING_DATA_BY_IDENTIFIER = 0x24
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    IO_CONTROL_BY_IDENTIFIER = 0x2F
    ROUTINE_CONTROL = 0x31
    REQUEST_DOWNLOAD = 0x34
    REQUEST_UPLOAD = 0x35
    TRANSFER_DATA = 0x36
    REQUEST_TRANSFER_EXIT = 0x37
    WRITE_MEMORY_BY_ADDRESS = 0x3D
    CLEAR_DIAGNOSTIC_INFORMATION = 0x14
    READ_DTC_INFORMATION = 0x19

class UDSSessionTypes(Enum):
    """UDS Session Types"""
    DEFAULT_SESSION = 0x01
    PROGRAMMING_SESSION = 0x02
    EXTENDED_DIAGNOSTIC_SESSION = 0x03

class UDSNegativeResponseCodes(Enum):
    """UDS Negative Response Codes (NRC)"""
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUBFUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH = 0x13
    RESPONSE_TOO_LONG = 0x14
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUBNET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION = 0x26
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    INVALID_KEY = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    SUBFUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F

class UDSECUSimulator:
    def __init__(self, host='localhost', port=6801):
        self.host = host
        self.port = port
        self.socket = None
        self.client_socket = None
        self.running = False
        
        # ECU State
        self.current_session = UDSSessionTypes.DEFAULT_SESSION
        self.security_level = 0  # 0 = locked, 1+ = unlocked levels
        self.security_seed = 0
        self.security_attempts = 0
        self.max_security_attempts = 3
        
        # Data Identifiers (DIDs) - Simulated ECU data
        self.data_identifiers = {
            0xF186: b"ECU Serial Number 12345",  # ECU Serial Number
            0xF190: b"VIN123456789ABCDEF",       # VIN
            0xF194: b"System Name ECU",          # System Name
            0xF195: b"System Version 1.0",      # System Version
            0xF18A: b"SW Version 2.1.0",        # Software Version
            0xF18C: b"SW Calibration ID",       # Software Calibration
            0xF1A0: b"Boot SW ID",              # Boot Software ID
            0xF1A1: b"Application SW ID",       # Application Software ID
            0xF1A2: b"Application Data ID",     # Application Data ID
        }
        
        # Diagnostic Trouble Codes (DTCs)
        self.stored_dtcs = [
            (0x123456, 0x12),  # DTC: 0x123456, Status: 0x12
            (0x789ABC, 0x08),  # DTC: 0x789ABC, Status: 0x08
        ]
        
        # Service handlers
        self.service_handlers: Dict[int, Callable] = {
            UDSServices.DIAGNOSTIC_SESSION_CONTROL.value: self._handle_diagnostic_session_control,
            UDSServices.ECU_RESET.value: self._handle_ecu_reset,
            UDSServices.SECURITY_ACCESS.value: self._handle_security_access,
            UDSServices.TESTER_PRESENT.value: self._handle_tester_present,
            UDSServices.READ_DATA_BY_IDENTIFIER.value: self._handle_read_data_by_identifier,
            UDSServices.WRITE_DATA_BY_IDENTIFIER.value: self._handle_write_data_by_identifier,
            UDSServices.CLEAR_DIAGNOSTIC_INFORMATION.value: self._handle_clear_diagnostic_information,
            UDSServices.READ_DTC_INFORMATION.value: self._handle_read_dtc_information,
            UDSServices.CONTROL_DTC_SETTING.value: self._handle_control_dtc_setting,
            UDSServices.ROUTINE_CONTROL.value: self._handle_routine_control,
        }
    
    def start_server(self):
        """Start the UDS server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.running = True
            
            print(f"UDS ECU Simulator started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    print(f"Client connected from {addr}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        print(f"Socket error: {e}")
                        
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop_server()
    
    def stop_server(self):
        """Stop the UDS server"""
        self.running = False
        if self.socket:
            self.socket.close()
    
    def _handle_client(self, client_socket):
        """Handle client connection"""
        try:
            while self.running:
                # Receive UDS request
                data = client_socket.recv(4096)
                if not data:
                    break
                
                print(f"Received: {data.hex().upper()}")
                
                # Process UDS request
                response = self._process_uds_request(data)
                
                if response:
                    print(f"Sending: {response.hex().upper()}")
                    client_socket.send(response)
                    
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            client_socket.close()
            print("Client disconnected")
    
    def _process_uds_request(self, request_data: bytes) -> Optional[bytes]:
        """Process incoming UDS request"""
        if len(request_data) < 1:
            return self._create_negative_response(0x00, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        service_id = request_data[0]
        
        # Check if service is supported
        if service_id not in self.service_handlers:
            return self._create_negative_response(service_id, UDSNegativeResponseCodes.SERVICE_NOT_SUPPORTED)
        
        try:
            # Call appropriate service handler
            return self.service_handlers[service_id](request_data)
        except Exception as e:
            print(f"Service handler error: {e}")
            return self._create_negative_response(service_id, UDSNegativeResponseCodes.GENERAL_REJECT)
    
    def _create_positive_response(self, service_id: int, data: bytes = b"") -> bytes:
        """Create positive response"""
        return bytes([service_id + 0x40]) + data
    
    def _create_negative_response(self, service_id: int, nrc: UDSNegativeResponseCodes) -> bytes:
        """Create negative response"""
        return bytes([0x7F, service_id, nrc.value])
    
    def _handle_diagnostic_session_control(self, request: bytes) -> bytes:
        """Handle Diagnostic Session Control service (0x10)"""
        if len(request) < 2:
            return self._create_negative_response(0x10, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        session_type = request[1]
        
        if session_type == UDSSessionTypes.DEFAULT_SESSION.value:
            self.current_session = UDSSessionTypes.DEFAULT_SESSION
        elif session_type == UDSSessionTypes.PROGRAMMING_SESSION.value:
            if self.security_level == 0:
                return self._create_negative_response(0x10, UDSNegativeResponseCodes.SECURITY_ACCESS_DENIED)
            self.current_session = UDSSessionTypes.PROGRAMMING_SESSION
        elif session_type == UDSSessionTypes.EXTENDED_DIAGNOSTIC_SESSION.value:
            self.current_session = UDSSessionTypes.EXTENDED_DIAGNOSTIC_SESSION
        else:
            return self._create_negative_response(0x10, UDSNegativeResponseCodes.SUBFUNCTION_NOT_SUPPORTED)
        
        # P2 Server Max timing (500ms = 0x01F4)
        # P2* Server Max timing (5000ms = 0x1388)
        timing_params = struct.pack(">HH", 0x01F4, 0x1388)
        
        return self._create_positive_response(0x10, bytes([session_type]) + timing_params)
    
    def _handle_ecu_reset(self, request: bytes) -> bytes:
        """Handle ECU Reset service (0x11)"""
        if len(request) < 2:
            return self._create_negative_response(0x11, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        reset_type = request[1]
        
        if reset_type == 0x01:  # Hard Reset
            # Simulate reset - reset security level
            self.security_level = 0
            self.current_session = UDSSessionTypes.DEFAULT_SESSION
            return self._create_positive_response(0x11, bytes([reset_type]))
        elif reset_type == 0x02:  # Key Off On Reset
            return self._create_positive_response(0x11, bytes([reset_type]))
        elif reset_type == 0x03:  # Soft Reset
            return self._create_positive_response(0x11, bytes([reset_type]))
        else:
            return self._create_negative_response(0x11, UDSNegativeResponseCodes.SUBFUNCTION_NOT_SUPPORTED)
    
    def _handle_security_access(self, request: bytes) -> bytes:
        """Handle Security Access service (0x27)"""
        if len(request) < 2:
            return self._create_negative_response(0x27, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        security_level = request[1]
        
        if security_level % 2 == 1:  # Odd = Request Seed
            if self.security_attempts >= self.max_security_attempts:
                return self._create_negative_response(0x27, UDSNegativeResponseCodes.EXCEEDED_NUMBER_OF_ATTEMPTS)
            
            # Generate seed (simplified - in real ECU this would be cryptographically secure)
            self.security_seed = int(time.time()) & 0xFFFF
            seed_bytes = struct.pack(">H", self.security_seed)
            
            return self._create_positive_response(0x27, bytes([security_level]) + seed_bytes)
            
        else:  # Even = Send Key
            if len(request) < 4:
                return self._create_negative_response(0x27, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
            
            provided_key = struct.unpack(">H", request[2:4])[0]
            expected_key = self._calculate_security_key(self.security_seed)
            
            if provided_key == expected_key:
                self.security_level = security_level // 2
                self.security_attempts = 0
                return self._create_positive_response(0x27, bytes([security_level]))
            else:
                self.security_attempts += 1
                return self._create_negative_response(0x27, UDSNegativeResponseCodes.INVALID_KEY)
    
    def _calculate_security_key(self, seed: int) -> int:
        """Calculate security key from seed (simplified algorithm)"""
        # This is a simplified example - real ECUs use complex cryptographic algorithms
        return (seed ^ 0xA5A5) + 0x1234
    
    def _handle_tester_present(self, request: bytes) -> bytes:
        """Handle Tester Present service (0x3E)"""
        if len(request) < 2:
            return self._create_negative_response(0x3E, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        subfunction = request[1]
        
        if subfunction == 0x00:  # Zero sub-function
            return self._create_positive_response(0x3E, bytes([subfunction]))
        else:
            return self._create_negative_response(0x3E, UDSNegativeResponseCodes.SUBFUNCTION_NOT_SUPPORTED)
    
    def _handle_read_data_by_identifier(self, request: bytes) -> bytes:
        """Handle Read Data By Identifier service (0x22)"""
        if len(request) < 3:
            return self._create_negative_response(0x22, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        response_data = b""
        i = 1
        
        while i < len(request) - 1:
            did = struct.unpack(">H", request[i:i+2])[0]
            
            if did in self.data_identifiers:
                response_data += struct.pack(">H", did) + self.data_identifiers[did]
            else:
                return self._create_negative_response(0x22, UDSNegativeResponseCodes.REQUEST_OUT_OF_RANGE)
            
            i += 2
        
        return self._create_positive_response(0x22, response_data)
    
    def _handle_write_data_by_identifier(self, request: bytes) -> bytes:
        """Handle Write Data By Identifier service (0x2E)"""
        if len(request) < 4:
            return self._create_negative_response(0x2E, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        if self.security_level == 0:
            return self._create_negative_response(0x2E, UDSNegativeResponseCodes.SECURITY_ACCESS_DENIED)
        
        did = struct.unpack(">H", request[1:3])[0]
        data = request[3:]
        
        if did in self.data_identifiers:
            self.data_identifiers[did] = data
            return self._create_positive_response(0x2E, struct.pack(">H", did))
        else:
            return self._create_negative_response(0x2E, UDSNegativeResponseCodes.REQUEST_OUT_OF_RANGE)
    
    def _handle_clear_diagnostic_information(self, request: bytes) -> bytes:
        """Handle Clear Diagnostic Information service (0x14)"""
        if len(request) < 4:
            return self._create_negative_response(0x14, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        if self.security_level == 0:
            return self._create_negative_response(0x14, UDSNegativeResponseCodes.SECURITY_ACCESS_DENIED)
        
        group_of_dtc = request[1:4]
        
        if group_of_dtc == b"\xFF\xFF\xFF":  # Clear all DTCs
            self.stored_dtcs.clear()
        
        return self._create_positive_response(0x14)
    
    def _handle_read_dtc_information(self, request: bytes) -> bytes:
        """Handle Read DTC Information service (0x19)"""
        if len(request) < 2:
            return self._create_negative_response(0x19, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        subfunction = request[1]
        
        if subfunction == 0x02:  # reportDTCByStatusMask
            if len(request) < 3:
                return self._create_negative_response(0x19, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
            
            status_mask = request
            response_data = bytes([subfunction, 0x00])  # Availability mask
            
            for dtc, status in self.stored_dtcs:
                if status & status_mask:
                    response_data += struct.pack(">LB", dtc, status)[1:]  # Skip first byte of DTC
            
            return self._create_positive_response(0x19, response_data)
        
        elif subfunction == 0x0A:  # reportSupportedDTC
            response_data = bytes([subfunction, 0x00])
            
            for dtc, status in self.stored_dtcs:
                response_data += struct.pack(">L", dtc)[1:]  # Skip first byte
            
            return self._create_positive_response(0x19, response_data)
        
        else:
            return self._create_negative_response(0x19, UDSNegativeResponseCodes.SUBFUNCTION_NOT_SUPPORTED)
    
    def _handle_control_dtc_setting(self, request: bytes) -> bytes:
        """Handle Control DTC Setting service (0x85)"""
        if len(request) < 2:
            return self._create_negative_response(0x85, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        subfunction = request[1]
        
        if subfunction == 0x01:  # DTC Setting On
            return self._create_positive_response(0x85, bytes([subfunction]))
        elif subfunction == 0x02:  # DTC Setting Off
            return self._create_positive_response(0x85, bytes([subfunction]))
        else:
            return self._create_negative_response(0x85, UDSNegativeResponseCodes.SUBFUNCTION_NOT_SUPPORTED)
    
    def _handle_routine_control(self, request: bytes) -> bytes:
        """Handle Routine Control service (0x31)"""
        if len(request) < 4:
            return self._create_negative_response(0x31, UDSNegativeResponseCodes.INCORRECT_MESSAGE_LENGTH)
        
        subfunction = request[1]
        routine_id = struct.unpack(">H", request[2:4])
        
        if subfunction == 0x01:  # Start Routine
            return self._create_positive_response(0x31, bytes([subfunction]) + struct.pack(">H", routine_id))
        elif subfunction == 0x02:  # Stop Routine
            return self._create_positive_response(0x31, bytes([subfunction]) + struct.pack(">H", routine_id))
        elif subfunction == 0x03:  # Request Routine Results
            return self._create_positive_response(0x31, bytes([subfunction]) + struct.pack(">H", routine_id) + b"\x00")
        else:
            return self._create_negative_response(0x31, UDSNegativeResponseCodes.SUBFUNCTION_NOT_SUPPORTED)

# Usage Example
if __name__ == "__main__":
    # Create and start the UDS ECU simulator
    simulator = UDSECUSimulator()
    
    try:
        simulator.start_server()
    except KeyboardInterrupt:
        print("\nShutting down simulator...")
        simulator.stop_server()
