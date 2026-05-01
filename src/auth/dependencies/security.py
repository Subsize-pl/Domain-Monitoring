from fastapi import Request, HTTPException, status

from core.utils.log.logger import get_logger

logger = get_logger(__name__)


async def same_origin_dependency(request: Request) -> None:
    expected_origin = f"{request.url.scheme}://{request.url.netloc}"

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    if origin:
        if origin != expected_origin:
            logger.warning(f"[SECURITY] Invalid origin: {origin}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid origin.",
            )
        return

    if referer:
        if not referer.startswith(expected_origin):
            logger.warning(f"[SECURITY] Invalid referer: {referer}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid referer.",
            )
        return

    logger.warning("[SECURITY] Missing origin and referer")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing origin.",
    )
