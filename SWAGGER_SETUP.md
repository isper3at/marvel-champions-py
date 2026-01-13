# Flask App Configuration with OpenAPI/Swagger UI

This guide shows how to integrate OpenAPI/Swagger UI into the Flask application.

## Option 1: Built-in Simple Swagger UI (Recommended)

The `src/swagger_ui.py` module provides Swagger UI integration without external dependencies.

### Setup

Update `app.py`:

```python
from src.swagger_ui import init_swagger_ui

app = Flask(__name__)

# ... other app configuration ...

# Initialize Swagger UI
init_swagger_ui(app)

# Now accessible at:
# - http://localhost:5000/api/docs (Swagger UI)
# - http://localhost:5000/api/redoc (ReDoc UI)
# - http://localhost:5000/openapi.yaml (OpenAPI spec)
```

### Access Points

- **Swagger UI**: http://localhost:5000/api/docs
- **ReDoc UI**: http://localhost:5000/api/redoc
- **OpenAPI YAML**: http://localhost:5000/openapi.yaml
- **Health Check**: http://localhost:5000/api/health

## Option 2: Using Flasgger (Advanced)

For automatic API documentation generation from docstrings:

### Installation

```bash
pip install flasgger
```

### Setup

```python
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

# Flasgger will auto-generate docs from docstrings
```

This approach generates docs from your Flask route docstrings automatically.

## Option 3: Using Flask-RESTX (Enterprise)

For large projects with full schema validation:

```bash
pip install flask-restx
```

```python
from flask_restx import Api, Resource, fields

api = Api(app, doc='/docs')

@api.route('/api/cards/<code>')
class CardResource(Resource):
    def get(self, code):
        """Get card by code"""
        pass
```

## Validating OpenAPI Spec

### Installation (Optional)

```bash
pip install openapi-spec-validator
```

### Validation

```python
from src.swagger_ui import validate_openapi_spec

is_valid, errors = validate_openapi_spec()
if not is_valid:
    print("OpenAPI spec validation errors:")
    for error in errors:
        print(f"  - {error}")
```

## Generating Client SDKs

### Python Client

```python
from src.swagger_ui import generate_client_stub

python_client = generate_client_stub('python')
with open('client_sdk.py', 'w') as f:
    f.write(python_client)
```

### TypeScript Client

```python
typescript_client = generate_client_stub('typescript')
with open('client_sdk.ts', 'w') as f:
    f.write(typescript_client)
```

## Testing the API

### Using Swagger UI "Try It Out"

1. Go to http://localhost:5000/api/docs
2. Find an endpoint
3. Click "Try It Out"
4. Fill in parameters
5. Click "Execute"
6. See response

### Using cURL

```bash
# Get card
curl -X GET http://localhost:5000/api/cards/01001a

# Search cards
curl -X GET "http://localhost:5000/api/cards/search?q=Spider"

# Import card
curl -X POST http://localhost:5000/api/cards/import \
  -H "Content-Type: application/json" \
  -d '{"code": "01001a"}'
```

### Using Python Requests

```python
import requests

# Get card
response = requests.get('http://localhost:5000/api/cards/01001a')
print(response.json())

# Import card
response = requests.post(
    'http://localhost:5000/api/cards/import',
    json={'code': '01001a'}
)
print(response.json())
```

## CORS Configuration

To allow Swagger UI from different origins:

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:8080"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

## OpenAPI Extensions

Add custom metadata to the spec:

```yaml
info:
  x-logo:
    url: 'https://example.com/logo.png'
    altText: 'Marvel Champions Logo'
  
  x-apiLifecycle:
    deprecated: false
    sunset: null

paths:
  /api/cards/{code}:
    x-rateLimit: 1000
    x-timeout: 30
```

## Monitoring & Analytics

Track API usage:

```python
from datetime import datetime

@app.before_request
def log_request():
    g.start_time = datetime.now()
    g.endpoint = request.endpoint
    logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def log_response(response):
    duration = (datetime.now() - g.start_time).total_seconds()
    logger.info(
        f"Response: {response.status_code} "
        f"{g.endpoint} ({duration:.3f}s)"
    )
    return response
```

## Security Best Practices

### Hide OpenAPI Docs in Production

```python
if app.config['ENV'] == 'production':
    # Disable Swagger UI in production
    app.config['SWAGGER_ENABLED'] = False
else:
    init_swagger_ui(app)
```

### Add API Key Authentication

```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/cards/<code>')
@require_api_key
def get_card(code):
    pass
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/cards/<code>')
@limiter.limit("60/hour")
def get_card(code):
    pass
```

## Deployment

### Docker

```dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

### Environment Variables

```bash
FLASK_ENV=production
API_HOST=0.0.0.0
API_PORT=5000
LOG_LEVEL=INFO
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.marvelchampions.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Troubleshooting

### Swagger UI Shows 404

- Check that `openapi.yaml` exists in project root
- Verify path is correct: `Path(__file__).parent.parent.parent / 'openapi.yaml'`
- Ensure Flask is serving static files correctly

### CORS Errors in Swagger UI

- Add CORS headers: `flask_cors.CORS(app)`
- Configure allowed origins in `OPENAPI_GUIDE.md`

### Endpoints Not Showing

- Verify path is in `openapi.yaml`
- Check operationId is unique
- Reload browser (hard refresh)
- Validate spec with `validate_openapi_spec()`

## References

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- [Swagger UI Documentation](https://github.com/swagger-api/swagger-ui)
- [ReDoc Documentation](https://redoc.ly/)
- [Flask Documentation](https://flask.palletsprojects.com/)
