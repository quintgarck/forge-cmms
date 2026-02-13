#!/usr/bin/env python
"""
Setup script for ForgeDB API REST
Automated installation and configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Execute a shell command with error handling."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return
    
    print("🔄 Creating virtual environment...")
    run_command(f"{sys.executable} -m venv venv", "Virtual environment creation")

def install_dependencies():
    """Install Python dependencies."""
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_path = "venv/bin/pip"
    
    run_command(f"{pip_path} install --upgrade pip", "Pip upgrade")
    run_command(f"{pip_path} install -r requirements.txt", "Dependencies installation")

def setup_environment_file():
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ .env file created from template")
        print("⚠️  Please edit .env file with your database configuration")
    else:
        print("❌ .env.example not found")

def check_database_connection():
    """Test database connection."""
    print("🔄 Testing database connection...")
    
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_path = "venv/bin/python"
    
    result = run_command(f"{python_path} manage.py check --database default", "Database connection test")
    
    if result is not None:
        print("✅ Database connection successful")
        return True
    else:
        print("❌ Database connection failed")
        print("⚠️  Please check your .env file configuration")
        return False

def run_migrations():
    """Run Django migrations."""
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_path = "venv/bin/python"
    
    run_command(f"{python_path} manage.py migrate", "Database migrations")

def collect_static_files():
    """Collect static files."""
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_path = "venv/bin/python"
    
    run_command(f"{python_path} manage.py collectstatic --noinput", "Static files collection")

def main():
    """Main setup function."""
    print("🚀 ForgeDB API REST - Automated Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Setup virtual environment
    setup_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment file
    setup_environment_file()
    
    # Test database connection
    db_ok = check_database_connection()
    
    if db_ok:
        # Run migrations
        run_migrations()
        
        # Collect static files
        collect_static_files()
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your database configuration")
        print("2. Create a superuser: python manage.py createsuperuser")
        print("3. Run the server: python manage.py runserver")
        print("4. Visit http://localhost:8000/swagger/ for API documentation")
    else:
        print("\n⚠️  Setup completed with database connection issues")
        print("Please check your .env file and database configuration")

if __name__ == "__main__":
    main()