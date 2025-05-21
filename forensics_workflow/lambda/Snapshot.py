import boto3
import time

def lambda_handler(event, context):
    instance_id = event.get('instance_id')
    if not instance_id:
        return {
            'statusCode': 400,
            'body': 'Instance ID is required'
        }
    
    region = 'ap-northeast-2'
    ec2 = boto3.client('ec2', region_name=region)
    snapshot_ids = []

    try:
        # Get all volumes attached to the instance
        volumes = ec2.describe_volumes(Filters=[{'Name': 'attachment.instance-id', 'Values': [instance_id]}])
        
        # Create snapshots of each volume
        for volume in volumes['Volumes']:
            snapshot = ec2.create_snapshot(VolumeId=volume['VolumeId'], Description=f'Forensic snapshot for {instance_id}')
            snapshot_ids.append(snapshot['SnapshotId'])
            time.sleep(10)
        
        # Wait for all snapshots to complete
        for snapshot_id in snapshot_ids:
            waiter = ec2.get_waiter('snapshot_completed')
            waiter.wait(SnapshotIds=[snapshot_id])
        
        # Launch new instance
        response = ec2.run_instances(
            ImageId='ami-0f7712b35774b7da2',
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            SecurityGroupIds=['sg-08a7c6f0047091082'],
            SubnetId='subnet-0dd9975ba001e5024',
            Placement={'AvailabilityZone': 'ap-northeast-2a'},
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'SNAPSHOT'
                        }
                    ]
                }
            ]
        )
        backup_instance_id = response['Instances'][0]['InstanceId']

        # Wait for the instance to be in running state
        instance_waiter = ec2.get_waiter('instance_running')
        instance_waiter.wait(InstanceIds=[backup_instance_id])

        device_index = 1
        for snapshot_id in snapshot_ids:
            volume = ec2.create_volume(SnapshotId=snapshot_id, AvailabilityZone='ap-northeast-2a')
            volume_id = volume['VolumeId']
            
            waiter = ec2.get_waiter('volume_available')
            waiter.wait(VolumeIds=[volume_id])
            
            ec2.attach_volume(
                InstanceId=backup_instance_id,
                VolumeId=volume_id,
                Device=f'/dev/sd{chr(102 + device_index)}'
            )
            device_index += 1

        return {
            'statusCode': 200,
            'body': 'Instance cloned and volumes attached',
            'backup_instance_id': backup_instance_id
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
