from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import zipfile
import boto3
import json
import io

S3_BUCKET_NAME = 'forensic-result-bucket'
SENDER = 'n4mchun@gmail.com'
RECIPIENT = 'n4mchun@gmail.com'

def lambda_handler(event, context):
    ses = boto3.client('ses')
    s3 = boto3.client('s3')

    prefix = event.get('final_key')
    if not prefix:
        return {
            'statusCode': 500,
            'body': 'nnn'
        }
        
    subject = 'Incident Response Report: Non-Volatile and Volatile Data'
    body_text = 'Please find the attached zip file containing the non-volatile and volatile data extracted from the compromised instance.'

    try:
        # Get list of files from S3
        s3_objects = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for obj in s3_objects.get('Contents', []):
                file_key = obj['Key']
                file_name = file_key[len(prefix):]
                file_obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
                file_content = file_obj['Body'].read()
                
                zip_file.writestr(file_name, file_content)
        
        zip_buffer.seek(0)
        
        # Create email message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        msg.attach(MIMEText(body_text))
        
        # Attach zip file
        part = MIMEApplication(zip_buffer.read())
        part.add_header('Content-Disposition', 'attachment', filename='report.zip')
        msg.attach(part)
        
        # Send email via SES
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
        'body': "Email sent with attachment report.zip"
    }
