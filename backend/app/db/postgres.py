"""
Database connection and operations
"""
import asyncio
import logging
from typing import Optional, AsyncGenerator
import asyncpg
import sqlite3
import aiosqlite
import os
from contextlib import asynccontextmanager

from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None
_sqlite_db: Optional[str] = None

async def init_db():
    """Initialize database connection"""
    global _pool, _sqlite_db
    
    if settings.database_url and "postgresql" in settings.database_url:
        # PostgreSQL for production
        try:
            _pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            await _create_postgres_tables()
            logger.info("PostgreSQL database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    else:
        # SQLite for development
        _sqlite_db = "interview_data.db"
        await _create_sqlite_tables()
        logger.info("SQLite database initialized")

@asynccontextmanager
async def get_db_session():
    """Get database session context manager"""
    if _pool:
        async with _pool.acquire() as conn:
            yield conn
    else:
        async with aiosqlite.connect(_sqlite_db) as conn:
            yield conn

async def _create_postgres_tables():
    """Create PostgreSQL tables"""
    global _pool
    
    schema_sql = """
    CREATE TABLE IF NOT EXISTS interviews (
        id VARCHAR(36) PRIMARY KEY,
        candidate_id VARCHAR(36) NOT NULL,
        candidate_name VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        difficulty VARCHAR(20) NOT NULL,
        session_data JSONB NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
    
    CREATE TABLE IF NOT EXISTS evaluations (
        id VARCHAR(36) PRIMARY KEY,
        interview_id VARCHAR(36) REFERENCES interviews(id),
        question_id VARCHAR(36) NOT NULL,
        deterministic_results JSONB,
        llm_results JSONB,
        final_score DECIMAL(3,2),
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_evaluations_interview_id ON evaluations(interview_id);
    """
    
    async with _pool.acquire() as conn:
        await conn.execute(schema_sql)

async def _create_sqlite_tables():
    """Create SQLite tables"""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS interviews (
        id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        candidate_name TEXT NOT NULL,
        role TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        session_data TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS evaluations (
        id TEXT PRIMARY KEY,
        interview_id TEXT,
        question_id TEXT NOT NULL,
        deterministic_results TEXT,
        llm_results TEXT,
        final_score REAL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews (id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
    CREATE INDEX IF NOT EXISTS idx_evaluations_interview_id ON evaluations(interview_id);
    """
    
    async with aiosqlite.connect(_sqlite_db) as conn:
        await conn.executescript(schema_sql)
        await conn.commit()
