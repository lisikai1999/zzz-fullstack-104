"""
数据库初始化与操作 - SQLite via aiosqlite
"""
import aiosqlite
import json
from datetime import datetime

DB_PATH = "simulation.db"


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS simulation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                params TEXT NOT NULL,
                results TEXT NOT NULL,
                record_type TEXT NOT NULL DEFAULT 'normal'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS optimization_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                target_turbidity REAL NOT NULL,
                raw_water_params TEXT NOT NULL,
                optimal_dosage REAL NOT NULL,
                cost REAL NOT NULL,
                method TEXT NOT NULL
            )
        """)
        await db.commit()


async def save_simulation(params: dict, results: dict, record_type: str = "normal"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO simulation_records (created_at, params, results, record_type) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), json.dumps(params), json.dumps(results), record_type),
        )
        await db.commit()


async def save_optimization(target_turbidity: float, raw_water_params: dict,
                            optimal_dosage: float, cost: float, method: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO optimization_records (created_at, target_turbidity, raw_water_params, optimal_dosage, cost, method) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), target_turbidity, json.dumps(raw_water_params), optimal_dosage, cost, method),
        )
        await db.commit()


async def get_history(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM simulation_records ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
