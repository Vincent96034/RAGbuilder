from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime)

    # Relationships
    rs_projects = relationship("ProjectModel", back_populates="rs_owner")
    rs_ext_api_usages = relationship("ExtApiUsageModel", back_populates="rs_user")


class ProjectModel(Base):
    __tablename__ = 'projects'

    project_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    rag_type_id = Column(Integer, ForeignKey('rag_type.rag_type_id'))
    title = Column(String)
    description = Column(Text)
    created_at = Column(DateTime)

    # Relationships
    rs_documents = relationship("DocumentModel", back_populates="rs_project")
    rs_gpt_schemas = relationship("GptSchemaModel", back_populates="rs_project")
    rs_owner = relationship("UserModel", back_populates="rs_projects")
    rs_rag_type = relationship("RagTypeModel", back_populates="rs_projects")


class DocumentModel(Base):
    __tablename__ = 'documents'

    document_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    file_metadata_id = Column(Integer, ForeignKey('file_metadata.file_metadata_id'))
    created_at = Column(DateTime)
    vectordb_destination = Column(String)
    file_type = Column(String)

    # Relationships
    rs_file_metadata = relationship("FileMetadataModel", uselist=False, back_populates="rs_document")
    rs_project = relationship("ProjectModel", back_populates="rs_documents")


class FileMetadataModel(Base):
    __tablename__ = 'file_metadata'

    file_metadata_id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_size = Column(Integer)
    author = Column(String)
    citation = Column(String)
    content_type = Column(String)

    # Relationships
    rs_document = relationship("DocumentModel", back_populates="rs_file_metadata")


class GptSchemaModel(Base):
    __tablename__ = 'gpt_schema'

    gpt_schema_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    schema = Column(Text)

    # Relationships
    rs_project = relationship("ProjectModel", back_populates="rs_gpt_schemas")


class RagTypeModel(Base):
    __tablename__ = 'rag_type'

    rag_type_id = Column(Integer, primary_key=True)
    title = Column(String)
    config = Column(Text)  # Assuming a JSON or similar configuration representation.
    
    # Relationships
    rs_projects = relationship("ProjectModel", back_populates="rs_rag_type")


class ExtApiUsageModel(Base):
    __tablename__ = 'ext_api_usage'

    ext_api_request_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    ext_api_request_type_id = Column(Integer, ForeignKey(
        'ext_api_types.ext_api_request_type_id'))
    payload = Column(Text)  # Assuming a JSON or similar payload representation.
    token_amount = Column(Integer)

    # Relationships
    rs_user = relationship("UserModel", back_populates="rs_ext_api_usages")
    rs_ext_api_type = relationship("ExtApiTypesModel", back_populates="rs_api_usages")


class ExtApiTypesModel(Base):
    __tablename__ = 'ext_api_types'

    ext_api_request_type_id = Column(Integer, primary_key=True)
    name = Column(String)
    cost_per_unit = Column(Integer)

    # Relationships
    rs_api_usages = relationship("ExtApiUsageModel", back_populates="rs_ext_api_type")