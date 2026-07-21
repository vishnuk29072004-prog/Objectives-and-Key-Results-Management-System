import sqlite3
import os
from datetime import datetime


def get_conn():
    db_path = os.path.abspath("okr.db")
    return sqlite3.connect(db_path, check_same_thread=False, timeout=30)


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL;")

        c.execute("""
        CREATE TABLE IF NOT EXISTS objectives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objective TEXT,
            deadline TEXT,
            category TEXT,
            owner TEXT
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objective_id INTEGER,
            task TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            deadline TEXT,
            weight REAL DEFAULT 1.0,
            FOREIGN KEY (objective_id) REFERENCES objectives(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            subtask TEXT,
            completed INTEGER DEFAULT 0,
            result TEXT,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            deadline TEXT,
            weight REAL DEFAULT 1.0,
            ai_generated_result TEXT,
            review_status TEXT DEFAULT 'pending',
            auto_executable INTEGER DEFAULT 1,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )""")

        conn.commit()


def insert_objective(objective, deadline, category=None, owner=None):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO objectives (objective, deadline, category, owner) VALUES (?, ?, ?, ?)",
                  (objective, deadline, category, owner))
        oid = c.lastrowid
        conn.commit()
        return oid


def insert_task(objective_id, task, deadline=None, weight=1.0):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO tasks (objective_id, task, deadline, weight) VALUES (?, ?, ?, ?)",
                  (objective_id, task, deadline, weight))
        tid = c.lastrowid
        conn.commit()
        return tid


def insert_subtask(task_id, subtask, deadline=None, weight=1.0):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO subtasks (task_id, subtask, deadline, weight) VALUES (?, ?, ?, ?)",
                  (task_id, subtask, deadline, weight))
        sid = c.lastrowid
        conn.commit()
        return sid


def get_tasks(objective_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE objective_id = ?", (objective_id,))
        tasks = c.fetchall()
        return tasks


def get_subtasks(task_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM subtasks WHERE task_id = ?", (task_id,))
        subtasks = c.fetchall()
        return subtasks


def get_subtask_by_id(subtask_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
        subtask = c.fetchone()
        return subtask


def mark_task_complete(task_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE tasks SET completed = 1, completed_at = ? WHERE id = ?", (datetime.now(), task_id))
        conn.commit()


def mark_subtask_complete(subtask_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE subtasks SET completed = 1, completed_at = ? WHERE id = ?", (datetime.now(), subtask_id))
        conn.commit()


def save_subtask_result(subtask_id, result, comment=None):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE subtasks SET result = ?, comment = ? WHERE id = ?", (result, comment, subtask_id))
        conn.commit()


def save_ai_generated_result(subtask_id, result):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE subtasks SET ai_generated_result = ? WHERE id = ?", (result, subtask_id))
        conn.commit()


def update_review_status(subtask_id, status):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE subtasks SET review_status = ? WHERE id = ?", (status, subtask_id))
        conn.commit()


def get_pending_review_subtasks(objective_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT subtasks.id, subtasks.subtask, subtasks.ai_generated_result, subtasks.comment
            FROM subtasks
            JOIN tasks ON subtasks.task_id = tasks.id
            WHERE tasks.objective_id = ?
            AND subtasks.auto_executable = 1
            AND subtasks.completed = 0
            AND subtasks.review_status = 'pending'
        """, (objective_id,))
        rows = c.fetchall()
        return rows


def update_task_progress_from_subtasks(task_id):
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM subtasks WHERE task_id = ?", (task_id,))
        subtasks = c.fetchall()

        if not subtasks:
            return

        completed_weight = sum(subtask[9] for subtask in subtasks if subtask[3] and subtask[9] is not None)
        total_weight = sum(subtask[9] for subtask in subtasks if subtask[9] is not None)

        if total_weight > 0 and completed_weight == total_weight:
            c.execute("UPDATE tasks SET completed = 1, completed_at = ? WHERE id = ?", (datetime.now(), task_id))

        conn.commit()


def get_objective_progress(objective_id):
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM tasks WHERE objective_id = ?", (objective_id,))
        tasks = c.fetchall()

        if not tasks:
            return 0.0

        total_task_weight = 0.0
        weighted_progress_sum = 0.0

        for task in tasks:
            task_id = task[0]
            task_weight = task[7] if task[7] is not None else 1.0
            total_task_weight += task_weight

            c.execute("SELECT * FROM subtasks WHERE task_id = ?", (task_id,))
            subtasks = c.fetchall()
            if not subtasks:
                task_completed = bool(task[3])
                task_progress_ratio = 1.0 if task_completed else 0.0
            else:
                sub_completed_weight = sum(st[9] for st in subtasks if st[3] and st[9] is not None)
                sub_total_weight = sum(st[9] for st in subtasks if st[9] is not None)
                task_progress_ratio = (sub_completed_weight / sub_total_weight) if sub_total_weight > 0 else 0.0

            weighted_progress_sum += task_progress_ratio * task_weight

        if total_task_weight <= 0:
            total_tasks_count = len(tasks)
            completed_tasks_count = sum(1 for task in tasks if task[3])
            return round((completed_tasks_count / total_tasks_count) * 100, 2) if total_tasks_count > 0 else 0.0

        return round((weighted_progress_sum / total_task_weight) * 100, 2)


def get_all_objectives():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id, objective, deadline, category, owner FROM objectives")
        rows = c.fetchall()
        return rows


def get_all_reminders():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT 
                s.subtask as name,
                s.deadline,
                o.objective
            FROM subtasks s
            JOIN tasks t ON s.task_id = t.id
            JOIN objectives o ON t.objective_id = o.id
            WHERE s.deadline IS NOT NULL 
            AND s.completed = 0
            AND s.deadline <= date('now', '+7 days')
            ORDER BY s.deadline ASC
        """)
        rows = c.fetchall()
        return [{"name": row[0], "deadline": row[1], "objective": row[2]} for row in rows]
