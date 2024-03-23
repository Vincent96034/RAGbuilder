import re
import logging
import pikepdf
from io import BytesIO

logger = logging.getLogger(__name__)


async def sanitize_text(content: bytes) -> bytes:
    """Sanitizes text content by removing non-printable characters and potentially
    dangerous patterns. This is a simplistic approach and might need adjustments
    based on specific use cases.
    """
    # Decode content (assuming UTF-8), remove non-printable characters, then encode again
    sanitized_content = re.sub(r'[^\x20-\x7E]+', '', content.decode('utf-8', errors='ignore')).encode('utf-8')
    return sanitized_content
    

async def sanitize_pdf(pdf_bytes: bytes) -> bytes:
    """
    Sanitizes a PDF file by removing JavaScript and other potentially unsafe elements.
    This function modifies the PDF content in memory and returns the sanitized PDF content as bytes.

    :param pdf_bytes: The original PDF content as bytes.
    :return: The sanitized PDF content as bytes.
    """
    try:
        # Use BytesIO to create a file-like object from the bytes
        with BytesIO(pdf_bytes) as pdf_io:
            # Open the PDF with pikepdf
            pdf = pikepdf.Pdf.open(pdf_io)

            # Perform the sanitization steps
            if '/Names' in pdf.Root and '/JavaScript' in pdf.Root['/Names']:
                del pdf.Root['/Names']['/JavaScript']
            for page in pdf.pages:
                if '/Annots' in page:
                    annotations = page['/Annots']
                    for annot in list(annotations):
                        if '/S' in annot and annot['/S'] == '/JavaScript':
                            annotations.remove(annot)

            # Save the sanitized PDF back to a BytesIO object
            output_io = BytesIO()
            pdf.save(output_io)

            # Return the sanitized PDF content as bytes
            return output_io.getvalue()
    except Exception as e:
        logger.error(f"Failed to sanitize PDF: {e}")
        raise RuntimeError(f"Failed to sanitize PDF: {e}")

