from fastapi import UploadFile, HTTPException
from app.file_handler.file_handlers import PDFHandler, TXTHandler


class FileHandler:
    """Factory class to get the appropriate handler for a file."""

    def __init__(self):
        self.handlers = {
            "pdf": PDFHandler,
            "txt": TXTHandler
        }

    def get_handler(self, file: UploadFile):
        extension = file.filename.split(".")[-1]
        handler = self.handlers.get(extension, None)
        if not handler:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: must be PDF or TXT, got {extension}")

        return handler(file=file)
