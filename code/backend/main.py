import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "ruido.db"))

app = Flask(__name__)


def utc_now_iso():
	return datetime.now(timezone.utc).isoformat()


def get_connection():
	connection = sqlite3.connect(DB_PATH)
	connection.row_factory = sqlite3.Row
	return connection


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


def seed_default_environment_if_empty():
	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute("SELECT COUNT(*) AS total FROM ambientes")
	total = cursor.fetchone()["total"]

	if total == 0:
		cursor.execute(
			"""
			INSERT INTO ambientes (nome, localizacao, sensor_id, limite_db, ativo, created_at)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			(
				"Sala Principal",
				"Laboratório",
				"e06a-001",
				65,
				1,
				utc_now_iso(),
			),
		)
		connection.commit()

	connection.close()


def row_to_dict(row):
	return {key: row[key] for key in row.keys()}


def json_error(message, status=400):
	response = jsonify({"erro": message})
	response.status_code = status
	return response


@app.after_request
def add_cors_headers(response):
	response.headers["Access-Control-Allow-Origin"] = "*"
	response.headers["Access-Control-Allow-Headers"] = "Content-Type"
	response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
	return response


@app.route("/", methods=["GET"])
def dashboard():
	return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/health", methods=["GET"])
def health():
	return jsonify(
		{
			"status": "ok",
			"service": "monitor-ruido-backend",
			"database": DB_PATH,
			"timestamp": utc_now_iso(),
		}
	)


@app.route("/api/ambientes", methods=["GET"])
def list_ambientes():
	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM ambientes ORDER BY id ASC")
	rows = cursor.fetchall()
	connection.close()
	return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/ambientes", methods=["POST"])
def create_ambiente():
	payload = request.get_json(silent=True) or {}
	nome = str(payload.get("nome", "")).strip()
	localizacao = str(payload.get("localizacao", "")).strip()
	sensor_id = str(payload.get("sensor_id", "")).strip()
	limite_db = payload.get("limite_db", 65)

	if not nome or not localizacao or not sensor_id:
		return json_error("Campos obrigatórios: nome, localizacao e sensor_id.", 400)

	try:
		limite_db = float(limite_db)
	except (TypeError, ValueError):
		return json_error("limite_db deve ser numérico.", 400)

	if limite_db < 0:
		return json_error("limite_db deve ser >= 0.", 400)

	connection = get_connection()
	cursor = connection.cursor()
	try:
		cursor.execute(
			"""
			INSERT INTO ambientes (nome, localizacao, sensor_id, limite_db, ativo, created_at)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			(nome, localizacao, sensor_id, limite_db, 1, utc_now_iso()),
		)
		ambiente_id = cursor.lastrowid
		connection.commit()
	except sqlite3.IntegrityError:
		connection.close()
		return json_error("sensor_id já cadastrado.", 409)

	cursor.execute("SELECT * FROM ambientes WHERE id = ?", (ambiente_id,))
	row = cursor.fetchone()
	connection.close()

	response = jsonify(row_to_dict(row))
	response.status_code = 201
	return response


@app.route("/api/ambientes/<int:ambiente_id>", methods=["PUT"])
def update_ambiente(ambiente_id):
	payload = request.get_json(silent=True) or {}

	fields = {}
	for key in ("nome", "localizacao", "sensor_id"):
		if key in payload:
			value = str(payload.get(key, "")).strip()
			if not value:
				return json_error(f"{key} não pode ser vazio.", 400)
			fields[key] = value

	if "limite_db" in payload:
		try:
			limite_db = float(payload.get("limite_db"))
		except (TypeError, ValueError):
			return json_error("limite_db deve ser numérico.", 400)
		if limite_db < 0:
			return json_error("limite_db deve ser >= 0.", 400)
		fields["limite_db"] = limite_db

	if "ativo" in payload:
		fields["ativo"] = 1 if bool(payload.get("ativo")) else 0

	if not fields:
		return json_error("Nenhum campo válido para atualização.", 400)

	set_clause = ", ".join([f"{field} = ?" for field in fields.keys()])
	values = list(fields.values()) + [ambiente_id]

	connection = get_connection()
	cursor = connection.cursor()

	cursor.execute("SELECT id FROM ambientes WHERE id = ?", (ambiente_id,))
	exists = cursor.fetchone()
	if not exists:
		connection.close()
		return json_error("Ambiente não encontrado.", 404)

	try:
		cursor.execute(f"UPDATE ambientes SET {set_clause} WHERE id = ?", values)
		connection.commit()
	except sqlite3.IntegrityError:
		connection.close()
		return json_error("sensor_id já cadastrado para outro ambiente.", 409)

	cursor.execute("SELECT * FROM ambientes WHERE id = ?", (ambiente_id,))
	row = cursor.fetchone()
	connection.close()

	return jsonify(row_to_dict(row))


@app.route("/api/medicoes", methods=["POST"])
def create_medicao():
	payload = request.get_json(silent=True) or {}
	sensor_id = str(payload.get("sensor_id", "")).strip()
	db = payload.get("db")

	if not sensor_id:
		return json_error("sensor_id é obrigatório.", 400)

	try:
		db = float(db)
	except (TypeError, ValueError):
		return json_error("db deve ser numérico.", 400)

	connection = get_connection()
	cursor = connection.cursor()

	cursor.execute("SELECT * FROM ambientes WHERE sensor_id = ? AND ativo = 1", (sensor_id,))
	ambiente = cursor.fetchone()
	if not ambiente:
		connection.close()
		return json_error("sensor_id não encontrado ou ambiente inativo.", 404)

	excedeu_limite = 1 if db > ambiente["limite_db"] else 0
	timestamp = utc_now_iso()

	cursor.execute(
		"""
		INSERT INTO medicoes (ambiente_id, db, excedeu_limite, created_at)
		VALUES (?, ?, ?, ?)
		""",
		(ambiente["id"], db, excedeu_limite, timestamp),
	)
	medicao_id = cursor.lastrowid

	alerta_criado = False
	if excedeu_limite:
		mensagem = f"Ruído acima do limite em {ambiente['nome']}: {db:.1f} dB"
		cursor.execute(
			"""
			INSERT INTO alertas (ambiente_id, medicao_id, mensagem, created_at)
			VALUES (?, ?, ?, ?)
			""",
			(ambiente["id"], medicao_id, mensagem, timestamp),
		)
		alerta_criado = True

	connection.commit()
	connection.close()

	return jsonify(
		{
			"ok": True,
			"ambiente_id": ambiente["id"],
			"sensor_id": sensor_id,
			"db": db,
			"limite_db": ambiente["limite_db"],
			"excedeu_limite": bool(excedeu_limite),
			"alerta_criado": alerta_criado,
			"timestamp": timestamp,
		}
	)


@app.route("/api/monitoramento", methods=["GET"])
def monitoramento():
	limit = request.args.get("limit", 40)
	try:
		limit = int(limit)
	except (TypeError, ValueError):
		limit = 40
	limit = max(1, min(limit, 200))

	connection = get_connection()
	cursor = connection.cursor()

	cursor.execute("SELECT * FROM ambientes ORDER BY id ASC")
	ambientes = [row_to_dict(row) for row in cursor.fetchall()]

	cursor.execute(
		"""
		SELECT m.id, m.ambiente_id, a.nome AS ambiente_nome, a.sensor_id,
			   a.limite_db, m.db, m.excedeu_limite, m.created_at
		FROM medicoes m
		JOIN ambientes a ON a.id = m.ambiente_id
		ORDER BY m.id DESC
		LIMIT ?
		""",
		(limit,),
	)
	medicoes = [row_to_dict(row) for row in cursor.fetchall()]

	latest_by_ambiente = {}
	for medicao in medicoes:
		ambiente_id = medicao["ambiente_id"]
		if ambiente_id not in latest_by_ambiente:
			latest_by_ambiente[ambiente_id] = medicao

	cursor.execute(
		"""
		SELECT id, ambiente_id, medicao_id, mensagem, created_at
		FROM alertas
		ORDER BY id DESC
		LIMIT 20
		"""
	)
	alertas = [row_to_dict(row) for row in cursor.fetchall()]

	connection.close()

	return jsonify(
		{
			"ambientes": ambientes,
			"ultima_por_ambiente": latest_by_ambiente,
			"medicoes": medicoes,
			"alertas": alertas,
			"servidor_em": utc_now_iso(),
		}
	)


@app.route("/api/alertas", methods=["GET"])
def list_alertas():
	limit = request.args.get("limit", 50)
	try:
		limit = int(limit)
	except (TypeError, ValueError):
		limit = 50
	limit = max(1, min(limit, 500))

	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute(
		"""
		SELECT al.id, al.ambiente_id, a.nome AS ambiente_nome, al.medicao_id,
			   al.mensagem, al.created_at
		FROM alertas al
		JOIN ambientes a ON a.id = al.ambiente_id
		ORDER BY al.id DESC
		LIMIT ?
		""",
		(limit,),
	)
	rows = cursor.fetchall()
	connection.close()

	return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/medicoes", methods=["OPTIONS"])
@app.route("/api/ambientes", methods=["OPTIONS"])
@app.route("/api/monitoramento", methods=["OPTIONS"])
@app.route("/api/alertas", methods=["OPTIONS"])
def options_ok():
	return ("", 204)


def bootstrap():
	init_db()
	seed_default_environment_if_empty()


if __name__ == "__main__":
	bootstrap()
	host = os.getenv("APP_HOST", "0.0.0.0")
	port = int(os.getenv("APP_PORT", "5000"))
	debug = os.getenv("APP_DEBUG", "0") == "1"
	app.run(host=host, port=port, debug=debug)