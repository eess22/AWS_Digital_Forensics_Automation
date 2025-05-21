import json
import boto3
import datetime

ec2 = boto3.client('ec2')
s3 = boto3.client('s3')

NETWORK_ACL_ID = 'acl-0909ad35a3f7ba3b2'
S3_BUCKET_NAME = 'malicious-ip-bucket'
MAX_ACL_ENTRIES = 20

def lambda_handler(event, context):
    try:
        # 이벤트에서 'detail' 키가 존재하는지 확인
        detail = event.get('detail')
        if not detail:
            raise KeyError("This event does not contain attacker's ipv4 address")
        
        ip_address = None
        if 'service' in detail and 'action' in detail['service']:
            action = detail['service']['action']
            if 'networkConnectionAction' in action and 'remoteIpDetails' in action['networkConnectionAction']:
                ip_address = action['networkConnectionAction']['remoteIpDetails'].get('ipAddressV4')
        
        if ip_address:
            try:
                # 네트워크 ACL 엔트리 목록 조회
                acl = ec2.describe_network_acls(NetworkAclIds=[NETWORK_ACL_ID])
                entries = acl['NetworkAcls'][0]['Entries']

                # IP 주소가 이미 존재하는지 확인
                if any(entry['CidrBlock'] == f"{ip_address}/32" and not entry['Egress'] for entry in entries):
                    result = f"IP {ip_address} is already present in Network ACL."
                else:
                    # ACL 엔트리 개수가 MAX_ACL_ENTRIES를 초과하면 오래된 엔트리 삭제
                    if len(entries) >= MAX_ACL_ENTRIES:
                        # Ingress 규칙만 고려
                        ingress_entries = [entry for entry in entries if not entry['Egress']]
                        if ingress_entries:
                            oldest_entry = min(ingress_entries, key=lambda x: x['RuleNumber'])
                            ec2.delete_network_acl_entry(
                                NetworkAclId=NETWORK_ACL_ID,
                                RuleNumber=oldest_entry['RuleNumber'],
                                Egress=False
                            )
                            ec2.delete_network_acl_entry(
                                NetworkAclId=NETWORK_ACL_ID,
                                RuleNumber=oldest_entry['RuleNumber'],
                                Egress=True
                            )
                            print(f"Deleted oldest ACL entry with RuleNumber: {oldest_entry['RuleNumber']}")

                    # 사용 가능한 RuleNumber 찾기
                    used_rule_numbers = {entry['RuleNumber'] for entry in entries}
                    available_rule_number = next(i for i in range(1, 32767) if i not in used_rule_numbers)

                    # 새로운 네트워크 ACL 엔트리 추가 (인바운드 및 아웃바운드)
                    ec2.create_network_acl_entry(
                        NetworkAclId=NETWORK_ACL_ID,
                        RuleNumber=available_rule_number,
                        Protocol='-1',
                        RuleAction='deny',
                        Egress=False,
                        CidrBlock=f"{ip_address}/32"
                    )
                    ec2.create_network_acl_entry(
                        NetworkAclId=NETWORK_ACL_ID,
                        RuleNumber=available_rule_number,
                        Protocol='-1',
                        RuleAction='deny',
                        Egress=True,
                        CidrBlock=f"{ip_address}/32"
                    )

                    result = f"IP {ip_address} added to Network ACL with RuleNumber {available_rule_number} (both inbound and outbound)."
            
            except Exception as e:
                result = f"Failed to add IP {ip_address} to Network ACL: {str(e)}"
            
        else:
            result = "No attacker IP found in the event."
        
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "result": result
        }
        
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"ip-ban-logs/{datetime.datetime.utcnow().isoformat()}.json",
            Body=json.dumps(log_entry)
        )
        
        return {
            'statusCode': 200,
            'body': result
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
