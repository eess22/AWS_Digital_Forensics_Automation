import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

S3_BUCKET_NAME = 'forensic-result-bucket'
SENDER = 'n4mchun@gmail.com'
RECIPIENT = 'n4mchun@gmail.com'

def lambda_handler(event, context):
    ses = boto3.client('ses')

    try:
        subject = 'Subject: AWS Security Alert: Potential Threat Detected'
        body_text = f'''
TIME = {event['time']}
REGION = {event['region']}
TYPE = {event['detail']['type']}
SUBNET ID = {event['detail']['resource']['instanceDetails']['networkInterfaces'][0]['subnetId']}
VPC ID = {event['detail']['resource']['instanceDetails']['networkInterfaces'][0]['vpcId']}'''

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        msg.attach(MIMEText(body_text))
        
        ses.send_raw_email(
            Source=SENDER,
            Destinations=[RECIPIENT],
            RawMessage={'Data': msg.as_string()}
        )
        
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }
    
    return {
        'statusCode': 200,
        'body': "Email sent with notification"
    }
