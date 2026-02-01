import os

import boto3
from botocore.exceptions import NoCredentialsError


class StorageService:
    def __init__(self):
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.access_key = os.getenv("R2_ACCESS_KEY_ID")
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("R2_BUCKET_NAME")
        self.public_domain = os.getenv("R2_PUBLIC_DOMAIN")

        if not self.access_key or not self.secret_key:
            print("WARNING: R2 credentials not found in env!")

        self.s3_client = boto3.client(
            service_name="s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
        )

    def upload_file(self, file_obj, object_name: str, content_type: str) -> str:
        try:
            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, object_name, ExtraArgs={"ContentType": content_type}
            )

            if self.public_domain:
                base_url = self.public_domain.rstrip("/")
                return f"{base_url}/{object_name}"
            return object_name

        except NoCredentialsError as e:
            print("Credentials not available")
            raise Exception("Ошибка конфигурации R2") from e
        except Exception as e:
            print(f"Failed to upload to R2: {e}")
            raise e


storage_service = StorageService()
