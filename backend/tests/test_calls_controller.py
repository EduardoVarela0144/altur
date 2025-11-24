"""
Unit and integration tests for calls controller
"""
import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from controllers.calls_controller import CallsController


class TestCallsController(unittest.TestCase):
    """Test cases for CallsController"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        # Mock database service
        self.mock_db = Mock()
        self.mock_db.create_call_record.return_value = "test_call_id_123"
        self.mock_db.get_call_by_id.return_value = {
            "id": "test_call_id_123",
            "filename": "test.wav",
            "transcript": "Test transcript",
            "summary": "Test summary",
            "tags": ["test-tag"]
        }
        self.mock_db.update_call_record.return_value = True
        self.mock_db.delete_call.return_value = True
        self.mock_db.get_all_calls.return_value = []
        
        # Mock STT service
        self.mock_stt = Mock()
        self.mock_stt.transcribe.return_value = "Test transcript from audio"
        
        # Mock LLM service
        self.mock_llm = Mock()
        self.mock_llm.analyze_transcript.return_value = {
            "summary": "Test summary",
            "tags": ["test-tag", "client wants to buy"]
        }
        
        with patch('controllers.calls_controller.DatabaseService', return_value=self.mock_db), \
             patch('controllers.calls_controller.get_stt_service', return_value=self.mock_stt), \
             patch('controllers.calls_controller.get_llm_service', return_value=self.mock_llm):
            self.controller = CallsController()
            self.controller.upload_folder = self.app.config['UPLOAD_FOLDER']
    
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    def test_allowed_file_extensions(self):
        """Test file extension validation"""
        self.assertTrue(self.controller._allowed_file("test.wav"))
        self.assertTrue(self.controller._allowed_file("test.MP3"))
        self.assertTrue(self.controller._allowed_file("test.m4a"))
        self.assertFalse(self.controller._allowed_file("test.txt"))
        self.assertFalse(self.controller._allowed_file("test.pdf"))
        self.assertFalse(self.controller._allowed_file("test"))
    
    def test_upload_no_file(self):
        """Test upload with no file provided"""
        with self.app.test_request_context():
            from flask import request
            response = self.controller.upload_and_process()
            self.assertEqual(response[1], 400)  # Status code
            data = response[0].get_json()
            self.assertFalse(data['success'])
            self.assertIn("No file provided", data['error'])
    
    def test_upload_empty_filename(self):
        """Test upload with empty filename"""
        with self.app.test_request_context(data={'file': (BytesIO(b''), '')}):
            from flask import request
            response = self.controller.upload_and_process()
            self.assertEqual(response[1], 400)
            data = response[0].get_json()
            self.assertFalse(data['success'])
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        with self.app.test_request_context(data={'file': (BytesIO(b'test'), 'test.txt')}):
            from flask import request
            response = self.controller.upload_and_process()
            self.assertEqual(response[1], 400)
            data = response[0].get_json()
            self.assertFalse(data['success'])
            self.assertIn("Invalid file type", data['error'])
    
    def test_upload_empty_file(self):
        """Test upload with empty file"""
        with self.app.test_request_context(data={'file': (BytesIO(b''), 'test.wav')}):
            from flask import request
            response = self.controller.upload_and_process()
            self.assertEqual(response[1], 400)
            data = response[0].get_json()
            self.assertFalse(data['success'])
            self.assertIn("empty", data['error'].lower())
    
    @patch('controllers.calls_controller.os.path.exists')
    @patch('controllers.calls_controller.os.path.getsize')
    def test_upload_success(self, mock_getsize, mock_exists):
        """Test successful file upload and processing"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        
        # Create a temporary audio file
        test_audio = BytesIO(b'fake audio content')
        test_audio.filename = 'test.wav'
        
        with self.app.test_request_context(data={'file': (test_audio, 'test.wav')}):
            from flask import request
            with patch('werkzeug.datastructures.FileStorage.save') as mock_save:
                response = self.controller.upload_and_process()
                self.assertEqual(response[1], 201)
                data = response[0].get_json()
                self.assertTrue(data['success'])
                self.assertIn('data', data)
    
    def test_get_all_calls(self):
        """Test getting all calls"""
        with self.app.test_request_context():
            response = self.controller.get_all()
            self.assertEqual(response[1], 200)
            data = response[0].get_json()
            self.assertTrue(data['success'])
            self.assertIn('data', data)
            self.assertIn('count', data)
    
    def test_get_all_calls_with_invalid_limit(self):
        """Test getting calls with invalid limit parameter"""
        with self.app.test_request_context('/?limit=invalid'):
            response = self.controller.get_all()
            self.assertEqual(response[1], 200)  # Should default to 100
            data = response[0].get_json()
            self.assertTrue(data['success'])
    
    def test_get_call_not_found(self):
        """Test getting a call that doesn't exist"""
        self.mock_db.get_call_by_id.return_value = None
        response = self.controller.get_one("nonexistent_id")
        self.assertEqual(response[1], 404)
        data = response[0].get_json()
        self.assertFalse(data['success'])
        self.assertIn("not found", data['error'].lower())
    
    def test_get_call_invalid_id(self):
        """Test getting a call with invalid ID format"""
        response = self.controller.get_one("")
        self.assertEqual(response[1], 400)
        data = response[0].get_json()
        self.assertFalse(data['success'])
    
    def test_delete_call_not_found(self):
        """Test deleting a call that doesn't exist"""
        self.mock_db.get_call_by_id.return_value = None
        response = self.controller.delete_one("nonexistent_id")
        self.assertEqual(response[1], 404)
        data = response[0].get_json()
        self.assertFalse(data['success'])
    
    def test_analytics(self):
        """Test analytics endpoint"""
        self.mock_db.get_all_calls.return_value = [
            {"tags": ["tag1", "tag2"], "transcript": "test"},
            {"tags": ["tag1"], "transcript": ""},
        ]
        response = self.controller.get_analytics()
        self.assertEqual(response[1], 200)
        data = response[0].get_json()
        self.assertTrue(data['success'])
        self.assertIn('total_calls', data['data'])
        self.assertIn('tag_distribution', data['data'])


class TestSTTService(unittest.TestCase):
    """Test cases for STT Service"""
    
    @patch('services.stt_service.whisper.load_model')
    def test_stt_service_initialization(self, mock_load):
        """Test STT service initialization"""
        mock_model = Mock()
        mock_load.return_value = mock_model
        
        from services.stt_service import STTService
        service = STTService(model_name="base")
        self.assertIsNotNone(service.model)
    
    @patch('services.stt_service.whisper.load_model')
    @patch('services.stt_service.os.path.exists')
    def test_transcribe_file_not_found(self, mock_exists, mock_load):
        """Test transcription with file not found"""
        mock_exists.return_value = False
        mock_model = Mock()
        mock_load.return_value = mock_model
        
        from services.stt_service import STTService
        service = STTService(model_name="base")
        
        with self.assertRaises(FileNotFoundError):
            service.transcribe("nonexistent.wav")


class TestLLMService(unittest.TestCase):
    """Test cases for LLM Service"""
    
    @patch('services.llm_service.OpenAI')
    def test_llm_service_initialization(self, mock_openai):
        """Test LLM service initialization"""
        import os
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        from services.llm_service import LLMService
        service = LLMService(api_key='test-key')
        self.assertIsNotNone(service.client)
    
    @patch('services.llm_service.OpenAI')
    def test_analyze_empty_transcript(self, mock_openai):
        """Test analysis with empty transcript"""
        import os
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        from services.llm_service import LLMService
        service = LLMService(api_key='test-key')
        
        result = service.analyze_transcript("")
        self.assertIn("summary", result)
        self.assertIn("tags", result)
        self.assertIn("no-transcript", result["tags"])


if __name__ == '__main__':
    unittest.main()

