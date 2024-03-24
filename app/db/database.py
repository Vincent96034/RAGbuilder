from firebase_admin import firestore

def get_db():
    try:
        db = firestore.client()
        yield db
    finally:
        pass
