"""
Initialize database and create tables.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.database import init_db, get_engine
from src.models import Base
from alembic import command
from alembic.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database and create initial migration."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path(project_root) / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Initialize database schema
        logger.info("Initializing database...")
        init_db()
        
        # Create alembic.ini if it doesn't exist
        alembic_ini = Path(project_root) / "alembic.ini"
        if not alembic_ini.exists():
            logger.error(f"alembic.ini not found at {alembic_ini}")
            return False
            
        # Initialize Alembic configuration
        alembic_cfg = Config(str(alembic_ini))
        
        # Set migrations directory in config
        migrations_dir = Path(project_root) / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        
        # Create initial migration
        logger.info("Creating initial migration...")
        command.revision(alembic_cfg,
                        message="Initial migration",
                        autogenerate=True)
        
        # Run the migration
        logger.info("Running database migration...")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    os.chdir(project_root)  # Change to project root directory
    init_database()