import os
import logging
import aiofiles
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def temporary_file(content, suffix="", sanitize_fn=None):
    """Context manager to create a temporary file with the given content and suffix.
    Automatically cleans up the file on exit.

    Args:
        - content: Content to be written to the temporary file.
        - suffix: Suffix for the temporary file name, e.g., '.pdf'.
        - sanitize_fn: Optional function to sanitize the content before writing.
    """
    try:
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            if sanitize_fn:
                content = await sanitize_fn(content)
                logger.debug(f"Sanitized content with {sanitize_fn.__name__}")
            await tmp.write(content)
            tmp_path = tmp.name
        yield tmp_path
    finally:
        os.unlink(tmp_path)

