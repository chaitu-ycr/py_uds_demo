class UdsClient:
    def __init__(self, server):
        self.server = server

    def send_request(self, request_data):
        converted_request = self.convert_request(request_data)
        if converted_request:
            response = self.server.process_request(converted_request)
            return self.convert_response(response)
        else:
            return "Invalid Request. Check console for more information."
    
    def convert_request(self, request):
        try:
            cleaned_request = request.replace("0X", "").replace(" ", "").upper()
            return [int(cleaned_request[i:i+2], 16) for i in range(0, len(cleaned_request), 2)]
        except Exception as e:
            print(e)
            return None
    
    def convert_response(self, response):
        return ' '.join(f"{byte:02X}" for byte in response)