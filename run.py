# File: run.py
# Purpose: Main entry point for running the anything-agents FastAPI application
# Dependencies: anything-agents/main.py, uvicorn
# Used by: Direct execution to start the development server

import os
import sys
import uvicorn
from pathlib import Path

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Add the anything-agents directory to Python path
current_dir = Path(__file__).parent
app_dir = current_dir / "anything-agents"
sys.path.insert(0, str(app_dir))

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

def load_environment():
    """Load environment variables from .env file if it exists."""
    env_file = current_dir / ".env.local"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print("   Using default environment variables")

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

def get_server_config():
    """Get server configuration from environment variables."""
    return {
        "host": os.getenv("HOST", "127.0.0.1"),
        "port": int(os.getenv("PORT", "8000")),
        "reload": os.getenv("RELOAD", "true").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "workers": int(os.getenv("WORKERS", "1")),
    }

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to run the FastAPI application."""
    print("🚀 Starting anything-agents FastAPI application...")
    
    # Load environment variables
    load_environment()
    
    # Get server configuration
    config = get_server_config()
    
    print(f"📍 Server will run on http://{config['host']}:{config['port']}")
    print(f"🔄 Reload mode: {'enabled' if config['reload'] else 'disabled'}")
    print(f"📝 Log level: {config['log_level']}")
    
    # Run the application
    try:
        uvicorn.run(
            "main:app",
            host=config["host"],
            port=config["port"],
            reload=config["reload"],
            log_level=config["log_level"],
            workers=config["workers"] if not config["reload"] else 1,
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
