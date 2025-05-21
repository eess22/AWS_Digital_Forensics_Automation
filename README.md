# AWS_Digital_Forensics_Automation

이 프로젝트는 AWS 환경에서 침해 사고 발생 시 디지털 포렌식 자동화 시스템을 구축하는 데 목적이 있습니다. GuardDuty 경고를 기점으로 Step Functions를 통한 자동화된 대응 및 분석을 수행합니다.

## 프로젝트 개요
 - 상황: 두 개의 가용 영역(AZ1, AZ2)으로 분산된 EC2 환경에서 AZ2 인스턴스가 침해됨
 - 목표: 실시간 위협 탐지 후, 포렌식 수집 및 분석을 자동화하여 빠른 대응 및 보고 체계를 구현
  
 ## 구성도

<img width="1279" alt="스크린샷 2025-05-21 17 18 06" src="https://github.com/user-attachments/assets/ebc6ca9f-a11f-4e4e-86a4-6137715ce735" />

## 주요 구성요소 및 프로세스

1. 위협 탐지 및 경고 발생
- Amazon GuardDuty: 침해 탐지 (예: AZ2 EC2 인스턴스 이상 탐지)
- Amazon EventBridge: 탐지 이벤트를 수신하고 자동 대응 트리거

2. 자동화된 대응 워크플로우 (Step Functions 기반)

	L1. 초기 대응
	- L1-1: SES를 통해 관리자에게 경고 메일 발송
	- L1-2: NACL, Security Group을 활용한 악성 IP 차단
	- L1-3: 휘발성 데이터 수집 (ex: 메모리, 네트워크 상태)

	L2. 휘발성 데이터 분석
	- S3에 저장된 휘발성 데이터를 분석

	L3. 인스턴스 격리
	- Security Group을 조정하여 격리

	L4. 스냅샷 생성
	- 침해된 EC2 인스턴스의 EBS 볼륨 스냅샷 생성

	L5. 비휘발성 데이터 수집
	- 스냅샷을 통해 별도 인스턴스에 마운트 후 데이터 수집

	L6. 데이터 분석
	- 분석 후 S3에 결과 저장

	L7. 메일 전송
	- 분석 결과를 SES로 관리 담당자에게 전송

## 사용 AWS 서비스
- GuardDuty: 위협 탐지
- EventBridge: 이벤트 트리거링
- Step Functions: 워크플로우 자동화
- EC2, EBS, S3: 데이터 수집 및 저장
- SES: 이메일 전송
- Security Group / NACL: 네트워크 통제

## 추가 발전 사항
- 포렌식 과정중 완전한 격리된 환경이 확실한지

