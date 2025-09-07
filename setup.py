#!/usr/bin/env python
"""
Setup script for AI Chat Assistant
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'media/documents',
        'vectordb',
        'static/css',
        'static/js',
        'templates/chat'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_environment():
    """Set up environment file"""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠️  Please edit .env file and add your Gemini API key")
    else:
        print("✓ .env file already exists")

def main():
    """Main setup function"""
    print("🚀 Setting up AI Chat Assistant...")
    print("=" * 50)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Setup environment
    print("\n🔧 Setting up environment...")
    setup_environment()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("❌ Failed to install dependencies. Please check your Python environment.")
        return False
    
    # Run migrations
    print("\n🗄️  Setting up database...")
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        print("❌ Failed to create migrations")
        return False
    
    if not run_command("python manage.py migrate", "Running migrations"):
        print("❌ Failed to run migrations")
        return False
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your Gemini API key")
    print("2. Run: python manage.py runserver")
    print("3. Open: http://127.0.0.1:8000")
    print("\n🔑 Get your Gemini API key from: https://makersuite.google.com/app/apikey")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
