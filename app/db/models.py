from typing import Optional
from dataclasses import dataclass

from firebase_admin._user_mgt import UserRecord
from google.cloud.firestore_v1.document import DocumentReference



class BaseModel:
    def to_dict(self):
        return self.__dict__

@dataclass
class UserModel(BaseModel):
    user_id: str
    email: str
    email_verified: bool
    disabled: bool
    display_name: str
    created_at: str

    @staticmethod
    def from_firebase(user: UserRecord):
        return UserModel(
            user_id=user.uid,
            email=user.email,
            email_verified=user.email_verified,
            disabled=user.disabled,
            display_name=user.display_name,
            created_at=user.user_metadata.creation_timestamp,
        )


@dataclass
class ProjectModel(BaseModel):
    project_id: str
    title: str
    description: str
    modeltype_id: str
    created_at: str
    updated_at: str
    user_id: str
    files: Optional[list] = None

    @staticmethod
    def from_firebase(project: DocumentReference):
        doc_data = project.to_dict()
        doc_data["project_id"] = project.id 
        return ProjectModel(**doc_data)


@dataclass
class ModelTypeModel(BaseModel):
    modeltype_id: str
    description: str
    title: str
    config: dict

    def from_firebase(model_type: DocumentReference):
        doc_data = model_type.to_dict()
        doc_data["modeltype_id"] = model_type.id
        return ModelTypeModel(**doc_data)


@dataclass
class FileModel(BaseModel):
    file_id: str
    project_id: str
    file_name: str
    file_type: str
    created_at: str
    vec_db_src: Optional[str] = None
    vec_db_key: Optional[str] = None
    metadata: Optional[dict] = None

    def from_firebase(file: DocumentReference):
        doc_data = file.to_dict()
        doc_data["file_id"] = file.id
        return FileModel(**doc_data)


# class DocumentModel(Base):
#     __tablename__ = 'documents'

#     document_id = Column(Integer, primary_key=True)
#     project_id = Column(Integer, ForeignKey('projects.project_id'))
#     file_metadata_id = Column(Integer, ForeignKey('file_metadata.file_metadata_id'))
#     created_at = Column(DateTime)
#     vectordb_destination = Column(String)
#     file_type = Column(String)

#     # Relationships
#     rs_file_metadata = relationship("FileMetadataModel", uselist=False, back_populates="rs_document")
#     rs_project = relationship("ProjectModel", back_populates="rs_documents")


# class FileMetadataModel(Base):
#     __tablename__ = 'file_metadata'

#     file_metadata_id = Column(Integer, primary_key=True)
#     file_name = Column(String)
#     file_size = Column(Integer)
#     author = Column(String)
#     citation = Column(String)
#     content_type = Column(String)

#     # Relationships
#     rs_document = relationship("DocumentModel", back_populates="rs_file_metadata")


# class GptSchemaModel(Base):
#     __tablename__ = 'gpt_schema'

#     gpt_schema_id = Column(Integer, primary_key=True)
#     project_id = Column(Integer, ForeignKey('projects.project_id'))
#     schema = Column(Text)

#     # Relationships
#     rs_project = relationship("ProjectModel", back_populates="rs_gpt_schemas")



# class ExtApiUsageModel(Base):
#     __tablename__ = 'ext_api_usage'

#     ext_api_request_id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('users.user_id'))
#     ext_api_request_type_id = Column(Integer, ForeignKey(
#         'ext_api_types.ext_api_request_type_id'))
#     payload = Column(Text)  # Assuming a JSON or similar payload representation.
#     token_amount = Column(Integer)

#     # Relationships
#     rs_user = relationship("UserModel", back_populates="rs_ext_api_usages")
#     rs_ext_api_type = relationship("ExtApiTypesModel", back_populates="rs_api_usages")


# class ExtApiTypesModel(Base):
#     __tablename__ = 'ext_api_types'

#     ext_api_request_type_id = Column(Integer, primary_key=True)
#     name = Column(String)
#     cost_per_unit = Column(Integer)

#     # Relationships
#     rs_api_usages = relationship("ExtApiUsageModel", back_populates="rs_ext_api_type")