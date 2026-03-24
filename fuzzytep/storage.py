import json
import sqlite3

from .analysis import (
    analyse_indicators,
    normalize_enterprise_payload,
    normalize_indicator_payload,
    resolve_industry_profile,
)
from .config import DATA_DIR, DB_PATH


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def row_to_dict(row):
    return dict(row) if row is not None else None


def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS enterprises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT NOT NULL,
                profile_code TEXT NOT NULL DEFAULT 'default',
                ownership TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS indicator_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enterprise_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                revenue REAL NOT NULL,
                profit REAL NOT NULL,
                costs REAL NOT NULL,
                profitability REAL NOT NULL,
                revenue_growth REAL NOT NULL DEFAULT 0,
                liquidity_ratio REAL NOT NULL DEFAULT 1.2,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enterprise_id INTEGER NOT NULL,
                indicator_entry_id INTEGER NOT NULL,
                efficiency_label TEXT NOT NULL,
                numeric_score REAL NOT NULL,
                comment TEXT NOT NULL,
                explanation TEXT NOT NULL,
                triggered_rules TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,
                FOREIGN KEY (indicator_entry_id) REFERENCES indicator_entries(id) ON DELETE CASCADE
            );
            """
        )
        _apply_schema_migrations(connection)


def _apply_schema_migrations(connection):
    indicator_columns = {row["name"] for row in connection.execute("PRAGMA table_info(indicator_entries)").fetchall()}
    enterprise_columns = {row["name"] for row in connection.execute("PRAGMA table_info(enterprises)").fetchall()}

    if "profile_code" not in enterprise_columns:
        connection.execute("ALTER TABLE enterprises ADD COLUMN profile_code TEXT NOT NULL DEFAULT 'default'")
        rows = connection.execute("SELECT id, industry FROM enterprises").fetchall()
        for row in rows:
            profile_code, _ = resolve_industry_profile(row["industry"])
            connection.execute("UPDATE enterprises SET profile_code = ? WHERE id = ?", (profile_code, row["id"]))

    if "revenue_growth" not in indicator_columns:
        connection.execute("ALTER TABLE indicator_entries ADD COLUMN revenue_growth REAL NOT NULL DEFAULT 0")
    if "liquidity_ratio" not in indicator_columns:
        connection.execute("ALTER TABLE indicator_entries ADD COLUMN liquidity_ratio REAL NOT NULL DEFAULT 1.2")


def list_enterprises():
    query = """
        SELECT
            e.*,
            COUNT(a.id) AS analyses_count,
            MAX(a.created_at) AS last_analysis_at,
            (
                SELECT ar.efficiency_label
                FROM analysis_results ar
                WHERE ar.enterprise_id = e.id
                ORDER BY ar.created_at DESC, ar.id DESC
                LIMIT 1
            ) AS last_efficiency_label
        FROM enterprises e
        LEFT JOIN analysis_results a ON a.enterprise_id = e.id
        GROUP BY e.id
        ORDER BY e.created_at DESC, e.id DESC
    """
    with get_connection() as connection:
        return [row_to_dict(row) for row in connection.execute(query).fetchall()]


def get_enterprise(enterprise_id):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM enterprises WHERE id = ?", (enterprise_id,)).fetchone()
    return row_to_dict(row)


def get_history(enterprise_id):
    query = """
        SELECT
            ar.id,
            ie.period,
            ie.revenue,
            ie.profit,
            ie.costs,
            ie.profitability,
            ie.revenue_growth,
            ie.liquidity_ratio,
            ar.efficiency_label,
            ar.numeric_score,
            ar.comment,
            ar.explanation,
            ar.triggered_rules,
            ar.created_at
        FROM analysis_results ar
        JOIN indicator_entries ie ON ie.id = ar.indicator_entry_id
        WHERE ar.enterprise_id = ?
        ORDER BY ar.created_at DESC, ar.id DESC
    """
    enterprise = get_enterprise(enterprise_id)
    with get_connection() as connection:
        rows = connection.execute(query, (enterprise_id,)).fetchall()

    history = []
    for row in rows:
        item = row_to_dict(row)
        saved_rules = json.loads(item["triggered_rules"])
        derived = analyse_indicators(
            {
                "period": item["period"],
                "revenue": item["revenue"],
                "profit": item["profit"],
                "costs": item["costs"],
                "profitability": item["profitability"],
                "revenue_growth": item["revenue_growth"],
                "liquidity_ratio": item["liquidity_ratio"],
            },
            enterprise=enterprise,
        )
        item.update(
            {
                "comment": derived["comment"],
                "explanation": derived["explanation"],
                "main_takeaway": derived["main_takeaway"],
                "strengths": derived["strengths"],
                "risks": derived["risks"],
                "actions": derived["actions"],
                "triggered_rules": derived["triggered_rules"] or saved_rules,
                "profit_margin": derived["profit_margin"],
                "cost_ratio": derived["cost_ratio"],
                "coverage_ratio": derived["coverage_ratio"],
                "revenue_growth": derived["revenue_growth"],
                "liquidity_ratio": derived["liquidity_ratio"],
                "industry_profile": derived["industry_profile"],
                "memberships": derived["memberships"],
            }
        )
        history.append(item)
    return history


def save_enterprise(payload, enterprise_id=None):
    enterprise = normalize_enterprise_payload(payload)
    with get_connection() as connection:
        if enterprise_id is None:
            cursor = connection.execute(
                """
                INSERT INTO enterprises (name, industry, profile_code, ownership, description, updated_at)
                VALUES (:name, :industry, :profile_code, :ownership, :description, CURRENT_TIMESTAMP)
                """,
                enterprise,
            )
            enterprise_id = cursor.lastrowid
        else:
            connection.execute(
                """
                UPDATE enterprises
                SET name = :name,
                    industry = :industry,
                    profile_code = :profile_code,
                    ownership = :ownership,
                    description = :description,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {**enterprise, "id": enterprise_id},
            )
    return get_enterprise(enterprise_id)


def delete_enterprise(enterprise_id):
    with get_connection() as connection:
        connection.execute("DELETE FROM enterprises WHERE id = ?", (enterprise_id,))


def save_analysis(enterprise_id, payload):
    enterprise = get_enterprise(enterprise_id)
    analysis = analyse_indicators(payload, enterprise=enterprise)
    indicators = normalize_indicator_payload(payload)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO indicator_entries (
                enterprise_id,
                period,
                revenue,
                profit,
                costs,
                profitability,
                revenue_growth,
                liquidity_ratio
            )
            VALUES (:enterprise_id, :period, :revenue, :profit, :costs, :profitability, :revenue_growth, :liquidity_ratio)
            """,
            {**indicators, "enterprise_id": enterprise_id},
        )
        indicator_entry_id = cursor.lastrowid
        cursor = connection.execute(
            """
            INSERT INTO analysis_results (
                enterprise_id,
                indicator_entry_id,
                efficiency_label,
                numeric_score,
                comment,
                explanation,
                triggered_rules
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                enterprise_id,
                indicator_entry_id,
                analysis["efficiency_label"],
                analysis["numeric_score"],
                analysis["comment"],
                analysis["explanation"],
                json.dumps(analysis["triggered_rules"], ensure_ascii=False),
            ),
        )
        analysis_id = cursor.lastrowid

    history_item = next(item for item in get_history(enterprise_id) if item["id"] == analysis_id)
    history_item["profit_margin"] = analysis["profit_margin"]
    history_item["cost_ratio"] = analysis["cost_ratio"]
    history_item["coverage_ratio"] = analysis["coverage_ratio"]
    history_item["revenue_growth"] = analysis["revenue_growth"]
    history_item["liquidity_ratio"] = analysis["liquidity_ratio"]
    history_item["industry_profile"] = analysis["industry_profile"]
    history_item["memberships"] = analysis["memberships"]
    return history_item
