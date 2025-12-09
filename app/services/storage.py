import boto3
import os
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ENV = os.getenv("APP_ENV", "development")  # default to development

if ENV == 'development':
    load_dotenv(".env.development")
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

class Storage:
    def __init__(self, ):
        self.s3 = boto3.client(
            service_name="s3",
            # Provide your Cloudflare account ID
            endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
            # Retrieve your S3 API credentials for your R2 bucket via API tokens (see: https://developers.cloudflare.com/r2/api/tokens)
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_ACCESS_KEY,
            region_name="auto", # Required by SDK but not used by R2
            )
        if ENV == "production":
            self.bucket_name = 'stories-prod'
        else:
            self.bucket_name = 'stories-dev'
    
    def delete_object(self, object_key: str):
        self.s3.delete_object(Bucket=self.bucket_name, Key=object_key)  
    def upload_file(self, file_name: str, object_name: str=None):
        """Upload a file to an S3 bucket

        :param bucket: Bucket to upload to
        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        # Upload the file
        try:
            response = self.s3.upload_file(file_name, self.bucket_name, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True
    
    def download_file(self, object_name: str, file_name: str):
        """Download a file from an S3 bucket

        :param bucket: Bucket to download from
        :param object_name: S3 object name
        :param file_name: File to download to
        :return: True if file was downloaded, else False
        """
        try:
            self.s3.download_file(self.bucket_name, object_name, file_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True
    
    def get_object(self, object_name: str) -> bytes:
        """Retrieve an object from the S3 bucket

        :param bucket: Bucket to retrieve from
        :param object_name: S3 object name
        :return: Object data as bytes
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=object_name)
            return response['Body'].read()
        except ClientError as e:
            logging.error(e)
            return b""

    def object_exists(self, object_name: str) -> bool:
        """Return True when the given object key exists in storage."""

        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                return False
            logging.error(e)
            return False
        