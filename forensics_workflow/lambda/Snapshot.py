import boto3
import time
import os

# --- 사용자 설정 필요 ---
# 1. 아래 IAM 인스턴스 프로파일 ARN을 사용자의 환경에 맞게 수정하세요.
#    이 프로파일은 'AmazonSSMManagedInstanceCore' 관리형 정책이 연결된 IAM 역할에 대한 것이어야 합니다.
#    분석용 EC2 인스턴스에 연결되어 SSM Run Command를 실행할 권한을 부여합니다.
IAM_INSTANCE_PROFILE_ARN = "arn:aws:iam::654654611672:instance-profile/EC2_SSM_ROLE"

# 2. 이 람다 함수를 실행하는 IAM 역할에는 다음 권한이 추가로 필요합니다:
#    - "iam:PassRole" (위에서 지정한 EC2 인스턴스 프로파일을 전달하기 위해)
#    - "ssm:SendCommand" (SSM Run Command를 실행하기 위해)
#    - "ssm:GetCommandInvocation" (SSM Run Command의 결과를 가져오기 위해)
#    - "ec2:CreateTags" (스냅샷에 해시 태그를 추가하기 위해)
# --------------------

def lambda_handler(event, context):
    instance_id = event.get('instance_id')
    if not instance_id:
        return {'statusCode': 400, 'body': 'Instance ID is required'}

    region = os.environ.get('AWS_REGION', 'ap-northeast-2')
    ec2 = boto3.client('ec2', region_name=region)
    ssm = boto3.client('ssm', region_name=region)
    
    snapshot_hashes = {}

    try:
        # 인스턴스에 연결된 모든 볼륨 가져오기
        volumes = ec2.describe_volumes(Filters=[{'Name': 'attachment.instance-id', 'Values': [instance_id]}])
        
        snapshot_ids = []
        for volume in volumes['Volumes']:
            snapshot = ec2.create_snapshot(
                VolumeId=volume['VolumeId'], 
                Description=f'Forensic snapshot for {instance_id}',
                TagSpecifications=[{'ResourceType': 'snapshot', 'Tags': [{'Key': 'SourceInstanceId', 'Value': instance_id}]}]
            )
            snapshot_ids.append(snapshot['SnapshotId'])
        
        if not snapshot_ids:
            return {'statusCode': 404, 'body': 'No volumes found for the instance.'}

        # 모든 스냅샷이 완료될 때까지 대기
        waiter = ec2.get_waiter('snapshot_completed')
        waiter.wait(SnapshotIds=snapshot_ids)
        
        # 분석용 EC2 인스턴스 시작
        response = ec2.run_instances(
            ImageId='ami-0c9c942bd7bf113a2', # Amazon Linux 2023 AMI
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            IamInstanceProfile={'Arn': IAM_INSTANCE_PROFILE_ARN},
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Forensic-Analyzer'}]}]
        )
        backup_instance_id = response['Instances'][0]['InstanceId']

        # 인스턴스가 실행 상태가 될 때까지 대기
        instance_waiter = ec2.get_waiter('instance_running')
        instance_waiter.wait(InstanceIds=[backup_instance_id])

        # 스냅샷으로부터 볼륨을 생성하고 분석용 인스턴스에 연결
        device_mappings = []
        for i, snapshot_id in enumerate(snapshot_ids):
            az = response['Instances'][0]['Placement']['AvailabilityZone']
            volume = ec2.create_volume(SnapshotId=snapshot_id, AvailabilityZone=az)
            volume_id = volume['VolumeId']
            
            waiter = ec2.get_waiter('volume_available')
            waiter.wait(VolumeIds=[volume_id])
            
            device_name = f'/dev/sd{chr(ord("f") + i)}'
            ec2.attach_volume(InstanceId=backup_instance_id, VolumeId=volume_id, Device=device_name)
            device_mappings.append({'SnapshotId': snapshot_id, 'DeviceName': device_name})
            time.sleep(5) # 볼륨 연결 안정화 시간

        # 연결된 각 볼륨의 해시 계산
        for item in device_mappings:
            snapshot_id = item['SnapshotId']
            device_name = item['DeviceName']
            
            # SSM Run Command를 사용하여 해시 계산
            command = f"sha256sum {device_name}"
            res = ssm.send_command(
                InstanceIds=[backup_instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={'commands': [command]},
                TimeoutSeconds=3600 # 대용량 볼륨을 위해 타임아웃을 길게 설정
            )
            command_id = res['Command']['CommandId']
            
            # 명령이 완료될 때까지 대기
            command_waiter = ssm.get_waiter('command_executed')
            command_waiter.wait(CommandId=command_id, InstanceId=backup_instance_id)

            # 결과 가져오기
            result = ssm.get_command_invocation(CommandId=command_id, InstanceId=backup_instance_id)
            
            if result['Status'] == 'Success':
                # 해시 값 파싱 (출력 형식: <hash>  <device_name>)
                hash_value = result['StandardOutputContent'].split()[0]
                snapshot_hashes[snapshot_id] = hash_value
                
                # 스냅샷에 해시 태그 추가
                ec2.create_tags(Resources=[snapshot_id], Tags=[{'Key': 'SHA256-Hash', 'Value': hash_value}])
            else:
                snapshot_hashes[snapshot_id] = f"Error: {result['StandardErrorContent']}"

        # 분석용 인스턴스 종료
        ec2.terminate_instances(InstanceIds=[backup_instance_id])

        return {
            'statusCode': 200,
            'body': 'Snapshots created, hashed, and tagged successfully.',
            'hashes': snapshot_hashes,
            'instance_id': instance_id
        }
    except Exception as e:
        # 오류 발생 시 생성된 리소스 정리 (선택적)
        if 'backup_instance_id' in locals() and backup_instance_id:
            ec2.terminate_instances(InstanceIds=[backup_instance_id])
        
        return {
            'statusCode': 500,
            'body': str(e)
        }
