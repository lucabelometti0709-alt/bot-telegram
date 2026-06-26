import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Inizializza il database creando le tabelle necessarie"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella per le attività
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella per le impostazioni utente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_task(self, description: str, date: str, time: str) -> int:
        """Aggiunge una nuova attività"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (description, date, time, completed)
            VALUES (?, ?, ?, 0)
        ''', (description, date, time))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def get_tasks_by_date(self, date: str) -> List[Dict]:
        """Ottiene tutte le attività per una specifica data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, description, date, time, completed
            FROM tasks
            WHERE date = ?
            ORDER BY time ASC
        ''', (date,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'description': row[1],
                'date': row[2],
                'time': row[3],
                'completed': bool(row[4])
            }
            for row in rows
        ]
    
    def get_all_tasks(self) -> List[Dict]:
        """Ottiene tutte le attività"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, description, date, time, completed
            FROM tasks
            ORDER BY date ASC, time ASC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'description': row[1],
                'date': row[2],
                'time': row[3],
                'completed': bool(row[4])
            }
            for row in rows
        ]
    
    def mark_completed(self, task_id: int) -> bool:
        """Marca un'attività come completata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET completed = 1 WHERE id = ?
        ''', (task_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def delete_task(self, task_id: int) -> bool:
        """Elimina un'attività"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def get_upcoming_tasks(self, date: str, time: str) -> List[Dict]:
        """Ottiene le attività future per una specifica data e ora"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, description, date, time, completed
            FROM tasks
            WHERE date = ? AND time > ? AND completed = 0
            ORDER BY time ASC
        ''', (date, time))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'description': row[1],
                'date': row[2],
                'time': row[3],
                'completed': bool(row[4])
            }
            for row in rows
        ]
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Ottiene un'attività specifica per ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, description, date, time, completed
            FROM tasks
            WHERE id = ?
        ''', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'description': row[1],
                'date': row[2],
                'time': row[3],
                'completed': bool(row[4])
            }
        return None
    
    def save_setting(self, key: str, value: str):
        """Salva una impostazione"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str) -> Optional[str]:
        """Ottiene una impostazione"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
