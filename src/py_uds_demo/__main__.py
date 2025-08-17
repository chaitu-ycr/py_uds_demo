# import os
# import socket
# import subprocess

# def run_streamlit():
#     try:
#         current_file_dir = os.path.dirname(__file__)
#         hostname_with_domainname = socket.getfqdn()
#         server_port = 9901
#         cmd = fr"streamlit run {current_file_dir}/uds_app.py --server.address {hostname_with_domainname} --server.port {server_port}"
#         subprocess.Popen(cmd, shell=True)
#     except Exception as e:
#         print(f'Error starting Streamlit web application: {e}')

# if __name__ == "__main__":
#     run_streamlit()
