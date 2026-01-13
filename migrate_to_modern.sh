#!/bin/bash
# migrate_to_modern.sh
# Automatically migrate project to modern Python structure

set -e

echo "========================================"
echo "Marvel Champions - Project Migration"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Not in project root (no .git directory found)"
    exit 1
fi

echo "✓ In project root"
echo ""

# Backup
echo "Creating backup..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "../$BACKUP_DIR"
cp -r . "../$BACKUP_DIR/"
echo "✓ Backup created at ../$BACKUP_DIR"
echo ""

# Create src directory structure
echo "Creating src/ directory structure..."
mkdir -p src/middleware
mkdir -p src/controllers
mkdir -p src/dto
mkdir -p logs
echo "✓ Directories created"
echo ""

# Move existing code to src/
echo "Moving code to src/..."

# List of directories to move
DIRS_TO_MOVE="entities boundaries repositories gateways interactors"

for dir in $DIRS_TO_MOVE; do
    if [ -d "$dir" ]; then
        echo "  Moving $dir/ to src/$dir/"
        mv "$dir" src/
    else
        echo "  ⚠ $dir/ not found, skipping"
    fi
done

# Move config.py if exists
if [ -f "config.py" ]; then
    echo "  Moving config.py to src/config.py"
    mv config.py src/
fi

# Create __init__.py files
echo "  Creating __init__.py files..."
touch src/__init__.py
touch src/middleware/__init__.py
touch src/controllers/__init__.py
touch src/dto/__init__.py

echo "✓ Code moved to src/"
echo ""

# Update imports
echo "Updating import statements..."

# Function to update imports in a file
update_imports() {
    local file=$1
    
    # Only process Python files
    if [[ $file == *.py ]]; then
        # Update imports
        sed -i.bak 's/^from entities/from src.entities/g' "$file"
        sed -i.bak 's/^from boundaries/from src.boundaries/g' "$file"
        sed -i.bak 's/^from repositories/from src.repositories/g' "$file"
        sed -i.bak 's/^from gateways/from src.gateways/g' "$file"
        sed -i.bak 's/^from interactors/from src.interactors/g' "$file"
        sed -i.bak 's/^from config/from src.config/g' "$file"
        sed -i.bak 's/^import config$/import src.config as config/g' "$file"
        
        # Remove backup file
        rm -f "${file}.bak"
    fi
}

export -f update_imports

# Update all Python files in src and tests
find src tests -name "*.py" -type f -exec bash -c 'update_imports "$0"' {} \;

echo "✓ Imports updated"
echo ""

# Create .env.example
echo "Creating .env.example..."
cat > .env.example << 'EOF'
# Flask Configuration
DEBUG=True
APP_HOST=0.0.0.0
APP_PORT=5000
SECRET_KEY=your-secret-key-here-change-in-production

# MongoDB Configuration
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=marvel_champions
MONGO_USERNAME=
MONGO_PASSWORD=

# MarvelCDB Configuration
MARVELCDB_URL=https://marvelcdb.com
RATE_LIMIT_CALLS=10
RATE_LIMIT_PERIOD=60
REQUEST_DELAY=0.5

# Image Storage Configuration
IMAGE_STORAGE_PATH=static/images/cards
MAX_IMAGE_SIZE=5242880
EOF
echo "✓ .env.example created"
echo ""

# Update .gitignore
echo "Updating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
*.egg

# Virtual environments
venv/
env/
ENV/
.venv
.poetry/

# Poetry
poetry.lock

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# Images
static/images/cards/*.jpg
static/images/cards/*.png

# Coverage
htmlcov/
.coverage
.pytest_cache/

# OS
.DS_Store
Thumbs.db

# Backup
backup_*/
EOF
echo "✓ .gitignore updated"
echo ""

# Check for Poetry
echo "Checking for Poetry..."
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found!"
    echo ""
    echo "Install Poetry with:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    echo ""
    echo "Then add to PATH:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "After installing Poetry, run:"
    echo "  poetry install"
    echo ""
else
    echo "✓ Poetry found: $(poetry --version)"
    echo ""
    
    # Check if pyproject.toml exists
    if [ -f "pyproject.toml" ]; then
        echo "Installing dependencies with Poetry..."
        poetry install
        echo "✓ Dependencies installed"
    else
        echo "⚠ pyproject.toml not found"
        echo "Please create it manually or copy from the artifact"
    fi
fi

echo ""
echo "========================================"
echo "Migration Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Review changes"
echo "2. Copy logging files from artifacts:"
echo "   - src/logging_config.py"
echo "   - src/middleware/audit_middleware.py"
echo "3. Copy pyproject.toml from artifact (if not exists)"
echo "4. Run: poetry install"
echo "5. Test: poetry run pytest tests/"
echo "6. Run app: poetry run python src/app.py"
echo ""
echo "Backup location: ../$BACKUP_DIR"
echo ""
