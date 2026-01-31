import boto3
from botocore.exceptions import NoCredentialsError
from core.config import settings


class StorageService:
    def __init__(self):
        # Настраиваем клиента boto3 для R2
        self.s3_client = boto3.client(
            service_name='s3',
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
            region_name="auto",  # Для R2 регион обычно 'auto'
        )
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_domain = settings.R2_PUBLIC_DOMAIN

    def upload_file(self, file_obj, object_name: str, content_type: str) -> str:
        """
        Загружает файл в R2 и возвращает публичную ссылку.
        """
        try:
            # Загружаем файл
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs={'ContentType': content_type}  # Важно, чтобы браузер понимал, что это картинка
            )

            # Формируем красивую ссылку
            # Если domain заканчивается на /, убираем его, чтобы не было двойного слэша
            base_url = self.public_domain.rstrip("/")
            return f"{base_url}/{object_name}"

        except NoCredentialsError:
            print("Credentials not available")
            raise Exception("Ошибка конфигурации R2")
        except Exception as e:
            print(f"Failed to upload to R2: {e}")
            raise e


# Создаем один экземпляр, чтобы импортировать его везде
storage_service = StorageService()