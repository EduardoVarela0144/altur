# Call Transcription Service - Altur

A comprehensive backend service that receives audio files, transcribes them using Whisper (STT), and analyzes the transcripts using OpenAI's LLM to generate summaries, tags, roles, emotions, intent, mood, and insights.

## Features

### Core Features ✅
- **Audio Transcription**: Uses OpenAI Whisper for speech-to-text conversion
- **LLM Analysis**: Analyzes transcripts to generate:
  - Summary of the call
  - Tags (e.g., "client wants to buy", "wrong number", "needs follow-up", "voicemail")
  - **Roles**: Detects who is speaking (agent, customer, manager, etc.)
  - **Emotions**: Detects emotional responses (happy, frustrated, angry, satisfied, etc.)
  - **Intent**: Primary user intent (purchase, complaint, information, support, etc.)
  - **Mood**: Overall mood of conversation (positive, negative, neutral, mixed)
  - **Insights**: Extracts valuable insights and key points
- **RESTful API**: Complete API for managing call records
- **Error Handling**: Comprehensive error handling for edge cases
- **Analytics**: Built-in analytics endpoint for call statistics
- **Export**: Export call records as JSON
- **Filtering**: Filter calls by tags and date range
- **Sorting**: Sort calls by upload time (newest first)
- **Tag Override**: Users can override AI-generated tags
- **Authentication**: Basic user authentication system

## Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- OpenAI API key
- FFmpeg (for audio processing)

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [FFmpeg website](https://ffmpeg.org/download.html)

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd altur/backend
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and fill in your configuration:
- `MONGO_URI`: MongoDB connection string (default: mongodb://localhost:27017/)
- `MONGO_DB_NAME`: Database name (default: call_transcription)
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `WHISPER_MODEL`: Whisper model size - options: tiny, base, small, medium, large (default: base)
- `UPLOAD_FOLDER`: Folder for uploaded files (default: uploads)
- `PORT`: Server port (default: 5000)
- `SECRET_KEY`: Secret key for authentication (auto-generated if not provided)

## Running Locally

### Development Mode

```bash
python main.py
```

The server will start on `http://localhost:5000`

### Production Mode (with Gunicorn)

```bash
gunicorn -c gunicorn.conf.py main:app
```

## Running with Docker Compose

The easiest way to run the entire stack:

```bash
docker-compose up -d
```

This will start:
- **MongoDB** on port 27017
- **Backend** service on port 5000
- **Frontend** service on port 5173

All services are connected via Docker network.

### Building Individual Docker Images

**Backend:**
```bash
cd backend
docker build -t altur-backend .
docker run -p 5000:5000 --env-file .env altur-backend
```

## API Endpoints

### Authentication

#### Register
```
POST /api/auth/register
Body: { "username": "user", "password": "pass", "email": "user@example.com" }
```

#### Login
```
POST /api/auth/login
Body: { "username": "user", "password": "pass" }
Response: { "success": true, "data": { "token": "...", "user_id": "...", ... } }
```

#### Logout
```
POST /api/auth/logout
Headers: Authorization: Bearer <token>
```

### Call Management

#### Upload and Process Call
```
POST /api/calls
Content-Type: multipart/form-data
Body: file (audio file)
Headers: Authorization: Bearer <token> (optional)

Response:
{
  "success": true,
  "data": {
    "id": "call_id",
    "filename": "call.wav",
    "transcript": "...",
    "summary": "...",
    "tags": ["tag1", "tag2"],
    "roles": {"speaker1": "agent", "speaker2": "customer"},
    "emotions": ["happy", "satisfied"],
    "intent": "purchase",
    "mood": "positive",
    "insights": ["insight1", "insight2"],
    "upload_timestamp": "2024-01-01T00:00:00"
  }
}
```

#### Get All Calls
```
GET /api/calls?tag=client%20wants%20to%20buy&start_date=2024-01-01&end_date=2024-12-31&limit=100&skip=0
```

Query Parameters:
- `tag` (optional): Filter by tag
- `start_date` (optional): Filter by start date (ISO format)
- `end_date` (optional): Filter by end date (ISO format)
- `limit` (optional): Max results (default: 100, max: 1000)
- `skip` (optional): Skip N results (default: 0)

#### Get Single Call
```
GET /api/calls/<call_id>
```

#### Update/Override Tags
```
PUT /api/calls/<call_id>/tags
Body: { "tags": ["new-tag1", "new-tag2"] }
```

#### Export Call as JSON
```
GET /api/calls/<call_id>/export
```

#### Get Analytics
```
GET /api/calls/analytics

Response:
{
  "success": true,
  "data": {
    "total_calls": 100,
    "total_tags": 250,
    "average_tags_per_call": 2.5,
    "calls_with_transcript": 95,
    "calls_without_transcript": 5,
    "tag_distribution": {
      "client wants to buy": 30,
      "needs follow-up": 25,
      ...
    }
  }
}
```

#### Delete Call
```
DELETE /api/calls/<call_id>
```

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

Or using unittest:

```bash
python -m unittest discover tests/
```

## Error Handling

The service handles various error cases:

- **Invalid file type**: Returns 400 with error message
- **File too large**: Returns 400 (max 100MB)
- **Empty file**: Returns 400
- **Missing file**: Returns 400
- **Empty transcript**: Handled gracefully with fallback message
- **LLM API failure**: Falls back to default values
- **Database errors**: Returns appropriate error codes
- **Invalid call ID**: Returns 400 or 404
- **Authentication errors**: Returns 401

## Architecture

### Components

1. **Database Service** (`services/database_service.py`)
   - MongoDB connection and operations
   - CRUD operations for call records
   - User and token management
   - Index management

2. **STT Service** (`services/stt_service.py`)
   - Whisper model integration
   - Audio transcription

3. **LLM Service** (`services/llm_service.py`)
   - OpenAI API integration
   - Transcript analysis
   - Summary, tags, roles, emotions, intent, mood, and insights generation

4. **Auth Service** (`services/auth_service.py`)
   - User registration and authentication
   - Token management
   - Password hashing

5. **Calls Controller** (`controllers/calls_controller.py`)
   - Request handling
   - File validation
   - Processing orchestration
   - Error handling

6. **Auth Controller** (`controllers/auth_controller.py`)
   - Authentication endpoints
   - User management

### Data Flow

1. Client uploads audio file → `POST /api/calls`
2. File validation (type, size, etc.)
3. File saved to disk
4. Call record created in database
5. Audio transcribed using Whisper
6. Transcript analyzed using OpenAI LLM (summary, tags, roles, emotions, intent, mood, insights)
7. Call record updated with all analysis data
8. Response returned to client

## Prompt Design

### LLM Analysis Prompt

The LLM service uses a structured prompt to extract comprehensive information:

**System Message:**
```
You are an expert assistant that analyzes phone call transcripts. Always respond with valid JSON only. Be thorough in detecting roles, emotions, intent, and extracting insights.
```

**User Prompt Structure:**
1. **Summary**: 2-3 sentence concise summary
2. **Tags**: From predefined list (client wants to buy, wrong number, needs follow-up, voicemail, complaint, inquiry, sale, support, other)
3. **Roles**: Identify speakers and their roles (agent, customer, manager, support)
4. **Emotions**: Detect emotional responses (happy, frustrated, angry, satisfied, confused, neutral)
5. **Intent**: Primary user intent (purchase, complaint, information, support, cancel, other)
6. **Mood**: Overall conversation mood (positive, negative, neutral, mixed)
7. **Insights**: 2-3 valuable insights or key points

**Why this design:**
- Structured JSON output ensures consistent parsing
- Multiple analysis dimensions provide comprehensive call understanding
- Predefined tag list ensures consistency while allowing flexibility
- Role detection helps understand conversation dynamics
- Emotion and mood tracking provides sentiment analysis
- Intent detection helps categorize call purpose
- Insights extraction provides actionable information

**Temperature**: 0.3 (lower for more consistent results)
**Max Tokens**: 1000 (increased to accommodate all fields)

## Design Decisions

### Why Whisper?
- Open-source and free
- High accuracy
- Supports multiple languages
- Can run locally (no API costs for transcription)

### Why OpenAI for Analysis?
- High-quality summaries and analysis
- Flexible tag generation
- Easy to customize prompts
- Reliable API
- Can extract multiple dimensions (roles, emotions, intent, mood, insights)

### Why MongoDB?
- Flexible schema for call records
- Easy to add new fields
- Good performance for read-heavy workloads
- Simple to set up and scale
- Native support for arrays and nested objects

### Why Basic Authentication?
- Simple to implement
- Sufficient for MVP
- Token-based for stateless API
- Can be extended to OAuth/JWT later

### Error Handling Strategy
- Fail fast for invalid inputs (400 errors)
- Graceful degradation for processing errors
- Partial records saved even if processing fails
- Detailed error messages for debugging
- Fallback values for LLM failures

## Improvements for Production

Given more time, I would add:

1. **Async Processing**: Use Celery or similar for background transcription
2. **Caching**: Cache LLM responses for similar transcripts
3. **Rate Limiting**: Prevent abuse of API endpoints
4. **Enhanced Authentication**: JWT tokens, refresh tokens, OAuth
5. **Webhooks**: Notify external systems when calls are processed
6. **Batch Processing**: Support uploading multiple files at once
7. **Audio Format Conversion**: Auto-convert unsupported formats
8. **Progress Tracking**: WebSocket updates for processing progress
9. **Retry Logic**: Automatic retries for failed LLM calls
10. **Monitoring**: Add logging, metrics, and alerting
11. **Multi-language Support**: Detect and handle multiple languages
12. **Speaker Diarization**: Better role detection using speaker separation
13. **Sentiment Analysis**: More detailed emotion detection
14. **Entity Extraction**: Extract names, phone numbers, emails from transcripts

## File Structure

```
backend/
├── controllers/
│   ├── calls_controller.py      # Request handling logic
│   └── auth_controller.py        # Authentication logic
├── routes/
│   ├── calls_routes.py           # API route definitions
│   └── auth_routes.py            # Auth route definitions
├── services/
│   ├── database_service.py       # MongoDB operations
│   ├── stt_service.py            # Whisper transcription
│   ├── llm_service.py             # OpenAI analysis
│   └── auth_service.py            # Authentication
├── middleware/
│   └── auth_middleware.py        # Auth decorators
├── tests/
│   └── test_calls_controller.py  # Unit and integration tests
├── uploads/                      # Uploaded audio files (created automatically)
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── docker-compose.yml            # Docker Compose configuration
├── Dockerfile                    # Backend Docker image
└── README.md                     # This file
```

## Troubleshooting

### Whisper model download fails
- Check internet connection
- Try a smaller model (tiny or base)
- Manually download model if needed

### OpenAI API errors
- Verify API key is correct
- Check API quota/limits
- Ensure model name is valid

### MongoDB connection errors
- Verify connection string format
- Check network connectivity
- Ensure MongoDB is running
- For Atlas: verify IP whitelist

### File upload errors
- Check `UPLOAD_FOLDER` permissions
- Ensure sufficient disk space
- Verify file format is supported

## License

[Your License Here]

## Author

[Your Name Here]
