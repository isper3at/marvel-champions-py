# Marvel Champions - EBI Architecture

A Python-based digital play application for Marvel Champions card game, built with clean EBI (Entity-Boundary-Interactor) architecture.

## Project Structure

```
marvel-champions-ebi/
├── entities/           # Domain models (immutable)
├── boundaries/         # Interfaces (ABC)
├── repositories/       # MongoDB implementations
├── gateways/          # External service integrations
├── interactors/       # Business logic
├── controllers/       # REST API endpoints
├── dto/               # Data Transfer Objects
├── utils/             # Utility functions
├── static/            # Static files & images
├── templates/         # HTML templates
├── config.py          # Configuration
└── app.py             # Application entry point
```

## Setup

1. **Install MongoDB**
   ```bash
   # macOS
   brew install mongodb-community
   brew services start mongodb-community
   
   # Ubuntu
   sudo apt install mongodb
   sudo systemctl start mongodb
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional)
   ```bash
   export MONGO_HOST=localhost
   export MONGO_PORT=27017
   export MONGO_DATABASE=marvel_champions
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

## Architecture Principles

- **Immutability**: All entities are frozen dataclasses
- **Dependency Inversion**: Depend on interfaces, not implementations
- **Single Responsibility**: Each class has one clear purpose
- **Type Safety**: Full type hints throughout

## Next Steps

Currently, the project has:
- ✅ Complete entity models
- ✅ All boundary interfaces
- ✅ Configuration system

Still to implement:
- ⏳ Repository implementations (MongoDB)
- ⏳ Gateway implementations (MarvelCDB, Image Storage)
- ⏳ Business logic (Interactors)
- ⏳ REST API (Controllers)
- ⏳ Frontend UI

## License

Personal/Educational use only. Respects Marvel Champions and MarvelCDB terms of service.
