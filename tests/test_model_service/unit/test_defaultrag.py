import os
import unittest
from unittest.mock import patch

from model_service.models import DefaultRAG


class TestDefaultRAG(unittest.TestCase):

    @patch('model_service.models.defaultrag.VectorStore')
    def setUp(self, MockVectorStore):
        # Mock the VectorStore passed during initialization
        self.mock_vectorstore = MockVectorStore()
        # Initialize Environment Variables
        os.environ["LANGCHAIN_API_KEY"] = "test_langchain_api_key"
        os.environ["OPENAI_API_KEY"] = "test_openai_api_key"
        # Initialize DefaultRAG with the mocked VectorStore
        self.model = DefaultRAG(self.mock_vectorstore)

    def tearDown(self):
        # Remove it to avoid side effects
        del os.environ["LANGCHAIN_API_KEY"]
        del os.environ["OPENAI_API_KEY"]

    def test_initialization(self):
        # Test if the model is initialized with correct default values
        self.assertEqual(self.model.chunk_size, 1500)
        self.assertEqual(self.model.chunk_overlap, 50)
        self.assertEqual(self.model.vectorstore, self.mock_vectorstore)

    @patch('model_service.models.DefaultRAG.invoke')
    def test_invoke(self, mock_invoke):
        # Prepare inputs and call invoke
        input_data = "Search query here."
        filters = {"namespace": "test_user_id", "project_id": "test-project"}
        namespace = "test_user_id"
        user_id = "user123"
        self.model.invoke(input_data=input_data, filters=filters,
                          namespace=namespace, user_id=user_id)

        # Ensure _invoke is called correctly
        mock_invoke.assert_called_once()
        _, kwargs = mock_invoke.call_args
        self.assertEqual(kwargs['user_id'], user_id)
        self.assertEqual(kwargs['input_data'], input_data)


if __name__ == '__main__':
    unittest.main()
