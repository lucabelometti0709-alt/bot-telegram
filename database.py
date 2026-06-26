import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional


class Database:
    def __init__(self, db_path: str = "tasks.db"):
        self.database_url = os.getenv("DATABASE_URL")
        self.db_path = db_path
        self.use_postgres = bool(self.database_url)
        self.init_db()

    @contextmanager
    def _connect(self):
        if self.use_postgres:
            try:
                import psycopg
            except ImportError as exc:
                raise RuntimeError(
                    "psycopg non installato. Aggiungi 'psycopg[binary]' a requirements.txt."
                ) from exc

            conn = psycopg.connect(self.database_url)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            try:
                yield conn
            finally:
                conn.close()

    def _cursor(self, conn):
        if self.use_postgres:
            return conn.cursor()
        return conn.cursor()

    def init_db(self):
        """Inizializza il database creando le tabelle necessarie."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        description TEXT NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        completed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )
            else:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TEXT NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        completed INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )
            conn.commit()

    def add_task(self, description: str, date: str, time: str) -> int:
        """Aggiunge una nuova attività."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    INSERT INTO tasks (description, date, time, completed)
                    VALUES (%s, %s, %s, FALSE)
                    RETURNING id
                    """,
                    (description, date, time),
                )
                task_id = cursor.fetchone()[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO tasks (description, date, time, completed)
                    VALUES (?, ?, ?, 0)
                    """,
                    (description, date, time),
                )
                task_id = cursor.lastrowid
            conn.commit()
            return int(task_id)

    def _rows_to_tasks(self, rows) -> List[Dict]:
        return [
            {
                "id": row[0],
                "description": row[1],
                "date": row[2],
                "time": row[3],
                "completed": bool(row[4]),
            }
            for row in rows
        ]

    def get_tasks_by_date(self, date: str) -> List[Dict]:
        """Ottiene tutte le attività per una specifica data."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                """
                SELECT id, description, date, time, completed
                FROM tasks
                WHERE date = %s
                ORDER BY time ASC
                """ if self.use_postgres else """
                SELECT id, description, date, time, completed
                FROM tasks
                WHERE date = ?
                ORDER BY time ASC
                """,
                (date,),
            )
            return self._rows_to_tasks(cursor.fetchall())

    def get_all_tasks(self) -> List[Dict]:
        """Ottiene tutte le attività."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                """
                SELECT id, description, date, time, completed
                FROM tasks
                ORDER BY date ASC, time ASC
                """
            )
            return self._rows_to_tasks(cursor.fetchall())

    def mark_completed(self, task_id: int) -> bool:
        """Marca un'attività come completata."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                """
                UPDATE tasks SET completed = TRUE WHERE id = %s
                """ if self.use_postgres else """
                UPDATE tasks SET completed = 1 WHERE id = ?
                """,
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Elimina un'attività."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s" if self.use_postgres else "DELETE FROM tasks WHERE id = ?",
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_upcoming_tasks(self, date: str, time: str) -> List[Dict]:
        """Ottiene le attività future per una specifica data e ora."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                """
                SELECT id, description, date, time, completed
                FROM tasks
                WHERE date = %s AND time > %s AND completed = FALSE
                ORDER BY time ASC
                """ if self.use_postgres else """
                SELECT id, description, date, time, completed
                FROM tasks
                WHERE date = ? AND time > ? AND completed = 0
                ORDER BY time ASC
                """,
                (date, time),
            )
            return self._rows_to_tasks(cursor.fetchall())

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Ottiene un'attività specifica per ID."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                """
                SELECT id, description, date, time, completed
                FROM tasks
                WHERE id = %s
                """ if self.use_postgres else """
                SELECT id, description, date, time, completed
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "description": row[1],
                    "date": row[2],
                    "time": row[3],
                    "completed": bool(row[4]),
                }
            return None

    def save_setting(self, key: str, value: str):
        """Salva una impostazione."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    INSERT INTO settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """,
                    (key, value),
                )
            else:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
                    """,
                    (key, value),
                )
            conn.commit()

    def get_setting(self, key: str) -> Optional[str]:
        """Ottiene una impostazione."""
        with self._connect() as conn:
            cursor = self._cursor(conn)
            cursor.execute(
                "SELECT value FROM settings WHERE key = %s" if self.use_postgres else "SELECT value FROM settings WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            return row[0] if row else None
