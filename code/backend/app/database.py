import sqlite3
from datetime import datetime, timezone

from flask import current_app


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_connection():
    connection = sqlite3.connect(current_app.config["DB_PATH"])
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row):
    return {key: row[key] for key in row.keys()}


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ambientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            localizacao TEXT NOT NULL,
            sensor_id TEXT NOT NULL UNIQUE,
            limite_db REAL NOT NULL DEFAULT 65,
            ativo INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS medicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ambiente_id INTEGER NOT NULL,
            db REAL NOT NULL,
            excedeu_limite INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ambiente_id) REFERENCES ambientes(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ambiente_id INTEGER NOT NULL,
            medicao_id INTEGER NOT NULL,
            mensagem TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ambiente_id) REFERENCES ambientes(id),
            FOREIGN KEY (medicao_id) REFERENCES medicoes(id)
        )
        """
    )

    connection.commit()
    connection.close()


def seed_default_environments():
    connection = get_connection()
    cursor = connection.cursor()

    defaults = [
        ("Sala Principal", "Laboratório", "e06a-001", 65.0),
        ("Biblioteca", "Bloco A", "e06a-002", 60.0),
    ]

    for nome, localizacao, sensor_id, limite_db in defaults:
        cursor.execute("SELECT id FROM ambientes WHERE sensor_id = ?", (sensor_id,))
        if cursor.fetchone():
            continue

        cursor.execute(
            """
            INSERT INTO ambientes (nome, localizacao, sensor_id, limite_db, ativo, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, localizacao, sensor_id, limite_db, 1, utc_now_iso()),
        )

    connection.commit()
    connection.close()
