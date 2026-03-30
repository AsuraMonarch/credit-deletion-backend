# Credit Deletion Backend

A Flask REST API backend for managing credit consultation requests.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file (use `.env.example` as template):
   ```bash
   cp .env.example .env
   ```

5. Run the application:
   ```bash
   python app.py
   ```

The server will start at `http://127.0.0.1:5000`

## API Endpoints

### Health Check
- `GET /health` - Check API and database health

### Consultation Requests
- `POST /consultation` - Create a new consultation request
- `GET /consultation` - List all consultation requests (with pagination)
- `GET /consultation/<id>` - Get a specific consultation
- `PUT /consultation/<id>` - Update a consultation
- `DELETE /consultation/<id>` - Delete a consultation
- `GET /consultation/stats` - Get consultation statistics

## Request/Response Examples

### Create Consultation
```bash
curl -X POST http://127.0.0.1:5000/consultation \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "214-801-5331",
    "message": "I need help with credit repair"
  }'
```

Response (201):
```json
{
  "success": true,
  "message": "Consultation request saved successfully",
  "data": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "214-801-5331",
    "message": "I need help with credit repair",
    "status": "pending",
    "created_at": "2026-03-30T10:30:00",
    "updated_at": "2026-03-30T10:30:00"
  }
}
```

### List Consultations
```bash
curl http://127.0.0.1:5000/consultation?page=1&per_page=20&status=pending
```

### Update Consultation Status
```bash
curl -X PUT http://127.0.0.1:5000/consultation/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_review"
  }'
```

### Get Statistics
```bash
curl http://127.0.0.1:5000/consultation/stats
```

## Database

SQLite database is automatically created at `instance/app.db` on first run.

## Development

For development, ensure `FLASK_ENV=development` in your `.env` file. This enables debug mode and auto-reloading.

## Production Deployment

For production, set `FLASK_ENV=production` and configure a proper database (PostgreSQL recommended).
