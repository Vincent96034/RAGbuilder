import pytest
from fastapi import HTTPException
#from google.cloud import firestore

from app.db.models import ProjectModel
from app.ops.project_ops import get_project #, update_project
#from app.schemas import UpdateProjectSchema


sample_projct = {
    "project_id": "test_project_id",
    "title": "Test Project",
    "description": "Test project description",
    "modeltype_id": "default-rag",
    "created_at": "2023-01-01T00:00",
    "updated_at": "2023-01-01T00:00:00Z",
    "user_id": "user123",
    "files": ["file1", "file2"]
}

sample_projct2 = {
    "project_id": "test_project_id2",
    "title": "Test Project2",
    "description": "Test project description2",
    "modeltype_id": "default-rag",
    "created_at": "2023-02-01T00:00",
    "updated_at": "2023-02-02T00:00:00Z",
    "user_id": "user123",
    "files": ["file1", "file2"]
}

sample_projects_data = [sample_projct, sample_projct2]


@pytest.mark.parametrize("doc_exists,expected_return,expected_exception", [
    (True, ProjectModel(**sample_projct), None),
    (False, None, HTTPException)
])
def test_get_project(mock_firestore_client, mocker, doc_exists, expected_return, expected_exception):
    mock_client, mock_doc_ref = mock_firestore_client
    
    # Setup the mock document
    mock_doc = mocker.Mock()
    mock_doc.exists = doc_exists
    mock_doc.to_dict.return_value = sample_projct
    mock_doc_ref.get.return_value = mock_doc
    
    # Mock the ProjectModel.from_firebase method if the document exists
    if doc_exists:
        mocker.patch('app.db.models.ProjectModel.from_firebase', return_value=expected_return)

    if expected_exception:
        # Verify the exception is raised for not found scenario
        with pytest.raises(expected_exception):
            get_project("non_existing_project_id", mock_client)
    else:
        # Call the function and verify for success scenario
        project = get_project("test_project_id", mock_client)
        assert project == expected_return


def test_update_project(mock_firestore_client, mocker):
    pass
    # mock_client, mock_doc_ref = mock_firestore_client
    # project_data = {
    #     "project_id": "test_project_id",
    #     "title": "Updated Project Title",
    #     "description": "Updated project description",
    #     "modeltype_id": "default-rag",}
    # # Create an instance of UpdateProjectSchema with the test data
    # update_project_schema_instance = UpdateProjectSchema(**project_data)
    
    # # Mock the model_dump method of UpdateProjectSchema to return project_data without 'project_id'
    # project_data_without_id = project_data.copy()
    # _ = project_data_without_id.pop("project_id")
    # mocker.patch.object(UpdateProjectSchema, 'model_dump', return_value=project_data_without_id)

    # # Execute the function under test
    # update_project(update_project_schema_instance, mock_client)
    
    # # Assert that Firestore's update method was called with the expected data
    # expected_data = project_data_without_id
    # expected_data["updated_at"] = firestore.SERVER_TIMESTAMP
    # mock_doc_ref.update.assert_called_once_with(expected_data)


def test_get_projects_for_user(mock_firestore_client, mocker):
    pass


def test_create_project():
    pass


def test_delete_project():
    pass


def test_check_user_project_access():
    pass

