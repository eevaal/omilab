import boto3
import os
from botocore.exceptions import NoCredentialsError
from fastapi import UploadFile, HTTPException
import uuid

# 1. Загружаем конфиги из .env
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
# Это ссылка, которую Cloudflare даст тебе, когда включишь Public Access (или твой домен)
R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN")


def get_s3_client():
    if not R2_ACCOUNT_ID or not R2_ACCESS_KEY_ID:
        print("CRITICAL: R2 Credentials not found!")
        return None

    return boto3.client(
        service_name='s3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    )


async def upload_file_to_r2(file: UploadFile, folder: str = "lectures") -> str:
    """
    Загружает файл в R2 и возвращает публичную ссылку.
    folder: папка внутри бакета (например, 'avatars' или 'lectures')
    """
    s3 = get_s3_client()
    if not s3:
        raise HTTPException(status_code=500, detail="Storage configuration error")

    # Генерируем уникальное имя файла, чтобы не перезатереть старые
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"

    try:
        # Читаем файл и заливаем
        # ExtraArgs={'ContentType': ...} важно, чтобы браузер понимал, что это видео/пдф, а не просто бинарник
        s3.upload_fileobj(
            file.file,
            R2_BUCKET_NAME,
            unique_filename,
            ExtraArgs={'ContentType': file.content_type}
        )

        # Формируем ссылку
        # Если R2_PUBLIC_DOMAIN не задан, вернем просто путь
        base_url = R2_PUBLIC_DOMAIN if R2_PUBLIC_DOMAIN else ""
        # Убираем слеш на конце домена, если он есть
        if base_url.endswith("/"):
            base_url = base_url[:-1]

        return f"{base_url}/{unique_filename}"

    except NoCredentialsError:
        print("Credentials not available")
        raise HTTPException(status_code=500, detail="S3 Credentials Error")
    except Exception as e:
        print(f"Error uploading to R2: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")