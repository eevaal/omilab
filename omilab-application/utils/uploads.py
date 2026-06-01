from fastapi import HTTPException, UploadFile, status

MAX_AVATAR_BYTES = 5 * 1024 * 1024
MAX_PDF_BYTES = 20 * 1024 * 1024


async def _enforce_size(file: UploadFile, max_bytes: int) -> None:
    total = 0

    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            await file.seek(0)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Файл слишком большой",
            )

    await file.seek(0)


async def validate_pdf_upload(file: UploadFile) -> None:
    await _enforce_size(file, MAX_PDF_BYTES)

    header = await file.read(5)
    await file.seek(0)

    if header != b"%PDF-":
        raise HTTPException(status_code=400, detail="Можно загружать только PDF")


async def validate_avatar_upload(file: UploadFile) -> tuple[str, str]:
    await _enforce_size(file, MAX_AVATAR_BYTES)

    header = await file.read(12)
    await file.seek(0)

    if header.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp", "image/webp"

    raise HTTPException(status_code=400, detail="Поддерживаются только JPG, PNG или WebP")
