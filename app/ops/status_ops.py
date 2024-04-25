from firebase_admin import firestore
from fastapi.exceptions import HTTPException

from app.utils import logger
from app.db.models import StatusModel
from app.schemas import CreateStatusSchema, UpdateStatusSchema


def create_status(status: CreateStatusSchema, db: firestore.client) -> StatusModel:
    status_ref = db.collection("status").document()
    data = status.model_dump()
    data["created_at"] = firestore.SERVER_TIMESTAMP
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    status_ref.set(data)
    doc = status_ref.get()
    if doc.exists:
        logger.debug(f"Created new status {doc}")
        return StatusModel.from_firebase(doc)
    else:
        raise Exception("Failed to create the status correctly.")


def get_status(status_id: str, db: firestore.client) -> StatusModel:
    doc_ref = db.collection("status").document(status_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Status not found")
    logger.debug(f"Got status {doc}")
    return StatusModel.from_firebase(doc)


def get_status_from_item(item_id: str, db: firestore.client) -> StatusModel:
    status_ref = db.collection("status").where("item_id", "==", item_id).limit(1)
    docs = status_ref.stream()
    if not docs:
        raise HTTPException(status_code=404, detail="Status not found")
    doc = list(docs)[0]
    logger.debug(f"Got status {doc}")
    return StatusModel.from_firebase(doc)


def update_status(status: UpdateStatusSchema, db: firestore.client) -> StatusModel:
    status_ref = db.collection("status").document(status.status_id)
    data = status.model_dump()
    # remove keys with none values
    data = {k: v for k, v in data.items() if v is not None}
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    status_ref.update(data)
    updated_doc = status_ref.get()  # fetch the data again
    if updated_doc.exists:
        logger.debug(f"Updated status {updated_doc}")
        return StatusModel.from_firebase(updated_doc)
    else:
        raise Exception("Failed to update the status correctly.")
