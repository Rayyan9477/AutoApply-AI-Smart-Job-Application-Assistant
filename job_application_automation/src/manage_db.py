"""
Command-line interface for database management.
"""
import os
import sys
import click
import logging
from pathlib import Path
from datetime import datetime
from alembic import command
from alembic.config import Config

from database import init_db, get_engine, check_database_connection, get_database_stats
from models import Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Database management command-line interface."""
    pass

@cli.command()
def init():
    """Initialize database and create tables."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

@cli.command()
def check():
    """Check database connection and health."""
    try:
        logger.info("Checking database connection...")
        success, error = check_database_connection()
        if success:
            logger.info("Database connection successful")
            stats = get_database_stats()
            logger.info("Database statistics:")
            logger.info(f"Status: {stats['status']}")
            logger.info("Connection pool:")
            for key, value in stats["connection_pool"].items():
                logger.info(f"  {key}: {value}")
            logger.info("Tables:")
            for table, data in stats["tables"].items():
                logger.info(f"  {table}: {data['row_count']} rows")
        else:
            logger.error(f"Database connection failed: {error}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        sys.exit(1)

@cli.command()
@click.option('--message', '-m', required=True, help='Migration message')
def make_migration(message):
    """Create a new database migration."""
    try:
        logger.info(f"Creating migration: {message}")
        
        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Create migration
        command.revision(alembic_cfg,
                        message=message,
                        autogenerate=True)
        
        logger.info("Migration created successfully")
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        sys.exit(1)

@cli.command()
@click.option('--revision', '-r', default='head',
              help='Revision to upgrade to (default: head)')
def upgrade(revision):
    """Upgrade database to a later version."""
    try:
        logger.info(f"Upgrading database to revision: {revision}")
        
        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run upgrade
        command.upgrade(alembic_cfg, revision)
        
        logger.info("Database upgraded successfully")
    except Exception as e:
        logger.error(f"Error upgrading database: {e}")
        sys.exit(1)

@cli.command()
@click.option('--revision', '-r', required=True,
              help='Revision to downgrade to')
def downgrade(revision):
    """Downgrade database to a previous version."""
    try:
        logger.info(f"Downgrading database to revision: {revision}")
        
        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run downgrade
        command.downgrade(alembic_cfg, revision)
        
        logger.info("Database downgraded successfully")
    except Exception as e:
        logger.error(f"Error downgrading database: {e}")
        sys.exit(1)

@cli.command()
def history():
    """Show database migration history."""
    try:
        logger.info("Getting migration history...")
        
        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Show history
        command.history(alembic_cfg)
    except Exception as e:
        logger.error(f"Error getting migration history: {e}")
        sys.exit(1)

@cli.command()
@click.option('--output', '-o', default='backup.sql',
              help='Output file name (default: backup.sql)')
def backup(output):
    """Backup database to a file."""
    try:
        logger.info(f"Backing up database to: {output}")
        
        engine = get_engine()
        if str(engine.url).startswith('sqlite'):
            # For SQLite, we can just copy the database file
            import shutil
            db_path = str(engine.url).replace('sqlite:///', '')
            backup_path = f"{db_path}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
        else:
            # For other databases, implement appropriate backup logic
            logger.error("Backup not implemented for this database type")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        sys.exit(1)

@cli.command()
def current():
    """Show current database revision."""
    try:
        logger.info("Getting current revision...")
        
        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Show current revision
        command.current(alembic_cfg)
    except Exception as e:
        logger.error(f"Error getting current revision: {e}")
        sys.exit(1)

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
def reset():
    """Reset database (WARNING: This will delete all data)."""
    try:
        logger.warning("Resetting database...")
        
        # Drop all tables
        engine = get_engine()
        Base.metadata.drop_all(engine)
        
        # Recreate tables
        Base.metadata.create_all(engine)
        
        logger.info("Database reset successfully")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        sys.exit(1)

@cli.group()
def monitor():
    """Monitor database health and performance."""
    pass

@monitor.command()
def health():
    """Check current database health."""
    try:
        logger.info("Checking database health...")
        from database import get_engine
        from database_monitor import DatabaseMonitorService
        
        monitor_service = DatabaseMonitorService(get_engine())
        import asyncio
        health_check = asyncio.run(monitor_service.check_database_health())
        
        if health_check["status"] == "healthy":
            logger.info("Database health check passed")
            logger.info("Connection pool stats:")
            for key, value in health_check["connection_pool"].items():
                logger.info(f"  {key}: {value}")
            
            if health_check.get("alerts"):
                logger.warning("Alerts found:")
                for alert in health_check["alerts"]:
                    logger.warning(f"  {alert['level']}: {alert['message']}")
                    
            if health_check.get("recommendations"):
                logger.info("Recommendations:")
                for rec in health_check["recommendations"]:
                    logger.info(f"  {rec['type']}: {rec['message']}")
        else:
            logger.error(f"Database health check failed: {health_check.get('error')}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        sys.exit(1)

@monitor.command()
@click.option('--days', '-d', default=1, help='Number of days to analyze')
def slow_queries(days):
    """Show slow query report."""
    try:
        logger.info(f"Generating slow query report for the last {days} days...")
        from database import get_engine
        from database_monitor import DatabaseMonitorService
        
        monitor_service = DatabaseMonitorService(get_engine())
        report = monitor_service.get_slow_query_report(days)
        
        logger.info(f"Found {report['total_slow_queries']} slow queries")
        if report['queries']:
            logger.info("Top slow queries:")
            for query in report['queries']:
                logger.info(f"\nQuery: {query['query']}")
                logger.info(f"Average time: {query['stats']['avg_time']:.2f}s")
                logger.info(f"Executions: {query['stats']['count']}")
                logger.info(f"Total time: {query['stats']['total_time']:.2f}s")
        
        logger.info("\nSummary:")
        logger.info(f"Total slow query time: {report['summary']['total_time']:.2f}s")
        logger.info(f"Average query time: {report['summary']['avg_time']:.2f}s")
    except Exception as e:
        logger.error(f"Error generating slow query report: {e}")
        sys.exit(1)

@monitor.command()
def performance():
    """Show current database performance metrics."""
    try:
        logger.info("Getting database performance metrics...")
        from database import get_engine
        from database_monitor import DatabaseMonitorService
        
        monitor_service = DatabaseMonitorService(get_engine())
        metrics = monitor_service.get_performance_metrics()
        
        logger.info("\nPerformance Score: {:.1f}/100".format(metrics["performance_score"]))
        
        logger.info("\nQuery Statistics:")
        for key, value in metrics["query_stats"].items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")
        
        logger.info("\nConnection Pool Status:")
        for key, value in metrics["pool_stats"].items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        sys.exit(1)

@monitor.command()
def analyze():
    """Analyze query patterns and provide optimization recommendations."""
    try:
        logger.info("Analyzing query patterns...")
        from database import get_engine
        from database_monitor import DatabaseMonitorService, analyze_query_patterns
        
        analysis = analyze_query_patterns()
        
        if analysis["recommendations"]:
            logger.info("\nOptimization Recommendations:")
            for rec in analysis["recommendations"]:
                logger.info(f"\n{rec['type'].upper()}:")
                logger.info(f"  {rec['message']}")
        
        if analysis["peak_times"]:
            logger.info("\nPeak Usage Times:")
            sorted_hours = sorted(
                analysis["peak_times"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for hour, count in sorted_hours[:5]:
                logger.info(f"  {hour:02d}:00 - {count} queries")
    except Exception as e:
        logger.error(f"Error analyzing query patterns: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()