# import pytest for testing
import pytest
from py_uds_demo.core.client import UdsClient
from py_uds_demo.core.server import UdsServer
from py_uds_demo.core.utils.uds_constants import Sid, Nrc

@pytest.fixture
def uds_client():
	return UdsClient()

@pytest.fixture
def uds_server():
	return UdsServer()

def test_send_request_positive_response(uds_client):
	# Use a supported SID (e.g., ReadDataByIdentifier = 0x22)
	sid = Sid().READ_DATA_BY_IDENTIFIER
	req = [sid]
	resp = uds_client.send_request(req, False)
	# Should be a positive response: [sid+0x40, 0x00]
	assert resp[0] == sid + 0x40
	assert resp[1] == 0x00

def test_send_request_formatted_response(uds_client):
	sid = Sid().READ_DATA_BY_IDENTIFIER
	req = [sid]
	resp = uds_client.send_request(req, True)
	# Should be a formatted string starting with green dot
	assert resp.startswith("🟢 ")
	assert "%02X" % (sid + 0x40) in resp

def test_send_request_negative_response(uds_client):
	# Use an unsupported SID (e.g., 0x99)
	req = [0x99]
	resp = uds_client.send_request(req, False)
	# Should be a negative response: [0x7F, 0x99, NRC]
	assert resp[0] == 0x7F
	assert resp[1] == 0x99
	assert resp[2] == Nrc().SERVICE_NOT_SUPPORTED

def test_send_request_negative_response_formatted(uds_client):
	req = [0x99]
	resp = uds_client.send_request(req, True)
	# Should be a formatted string starting with red dot
	assert resp.startswith("🔴 ")
	assert "7F 99" in resp

def test_server_supported_services(uds_server):
	# Should contain all SIDs
	sids = uds_server.supported_services
	assert Sid().DIAGNOSTIC_SESSION_CONTROL in sids
	assert Sid().READ_DATA_BY_IDENTIFIER in sids

def test_server_process_request_positive(uds_server):
	sid = Sid().READ_DATA_BY_IDENTIFIER
	resp = uds_server.process_request([sid])
	assert resp[0] == sid + 0x40

def test_server_process_request_negative(uds_server):
	resp = uds_server.process_request([0x99])
	assert resp[0] == 0x7F
	assert resp[1] == 0x99
	assert resp[2] == Nrc().SERVICE_NOT_SUPPORTED
