import boto3

def lambda_handler(event, context):
    instance_id = event['instance_id']  
    quarantine_security_group = 'sg-086e7de355e928cea'
    target_group_arn = 'arn:aws:elasticloadbalancing:ap-northeast-2:654654611672:targetgroup/TG/d094787db6a7427b' #arn:aws:elasticloadbalancing:ap-northeast-2:654654611672:loadbalancer/app/ALB/600a6b0810c73a8d

    # AWS 리전을 명시적으로 지정
    region = 'ap-northeast-2'
    
    ec2 = boto3.client('ec2', region_name=region)
    elbv2 = boto3.client('elbv2', region_name=region)

    try:
      
        # ALB Target Group에서 인스턴스 제거
        elbv2.deregister_targets(
            TargetGroupArn=target_group_arn,
            Targets=[{'Id': instance_id}]
        )
        
         # 인스턴스의 보안 그룹을 격리 보안 그룹으로 변경
        ec2.modify_instance_attribute(InstanceId=instance_id, Groups=[quarantine_security_group])

        return {
            'statusCode': 200,
            'body': 'Instance isolated and removed from target group',
            'instance_id': instance_id
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
