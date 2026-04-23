"""
Run this script once to create/migrate all tables:
    uv run python -m db.init_db
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Full DDL for fresh installs
DDL = """
CREATE TABLE IF NOT EXISTS inventories (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    inventory_id INT UNSIGNED NOT NULL,
    item_name    VARCHAR(255) NOT NULL,
    quantity     DECIMAL(10, 3) NOT NULL DEFAULT 0,
    unit         VARCHAR(50)  NOT NULL DEFAULT '',
    category     VARCHAR(100),
    expires_at   DATE,
    added_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_inventory_item (inventory_id, item_name),
    FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS receipts (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_path       VARCHAR(512),
    raw_llm_output   TEXT,
    processed_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS receipt_items (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    receipt_id  INT UNSIGNED NOT NULL,
    item_name   VARCHAR(255) NOT NULL,
    quantity    DECIMAL(10, 3),
    unit        VARCHAR(50),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meal_plans (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    week_of    DATE      NOT NULL COMMENT 'Monday of the planned week',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_week (week_of)
);

CREATE TABLE IF NOT EXISTS meal_plan_entries (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    meal_plan_id INT UNSIGNED NOT NULL,
    day_of_week  ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
    meal_type    ENUM('breakfast','lunch','dinner','snack') NOT NULL,
    meal_name    VARCHAR(255) NOT NULL,
    description  TEXT,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vegetarian          TINYINT(1)   NOT NULL DEFAULT 0,
    active_inventory_id INT UNSIGNED DEFAULT NULL,
    FOREIGN KEY (active_inventory_id) REFERENCES inventories(id) ON DELETE SET NULL
);
"""


def _migrate(conn, db_name: str) -> None:
    """Apply schema migrations so existing databases are brought up to date."""
    with conn.cursor() as cur:
        cur.execute(f"USE `{db_name}`")

        # 1. Create inventories table if missing
        cur.execute("CREATE TABLE IF NOT EXISTS inventories ("
                    "  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
                    "  name VARCHAR(255) NOT NULL,"
                    "  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    ")")
        conn.commit()

        # 2. Seed a Default inventory if the table is empty
        cur.execute("SELECT COUNT(*) AS n FROM inventories")
        if cur.fetchone()["n"] == 0:
            cur.execute("INSERT INTO inventories (name) VALUES ('Default')")
            conn.commit()

        cur.execute("SELECT id FROM inventories ORDER BY id LIMIT 1")
        default_inv_id = cur.fetchone()["id"]

        # 3. Add inventory_id column to inventory if missing
        cur.execute("SHOW COLUMNS FROM inventory LIKE 'inventory_id'")
        if not cur.fetchone():
            cur.execute(
                f"ALTER TABLE inventory "
                f"ADD COLUMN inventory_id INT UNSIGNED NOT NULL DEFAULT {default_inv_id} AFTER id"
            )
            # Drop the old UNIQUE constraint on item_name alone
            cur.execute(
                "SELECT INDEX_NAME FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'inventory' "
                "AND COLUMN_NAME = 'item_name' AND NON_UNIQUE = 0 AND INDEX_NAME != 'PRIMARY'",
                (db_name,),
            )
            for row in cur.fetchall():
                cur.execute(f"ALTER TABLE inventory DROP INDEX `{row['INDEX_NAME']}`")
            # Add new composite unique + FK
            cur.execute(
                "ALTER TABLE inventory "
                "ADD UNIQUE KEY uq_inventory_item (inventory_id, item_name),"
                "ADD CONSTRAINT fk_inv_inventories "
                "  FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE"
            )
            conn.commit()

        # 4. Add active_inventory_id to user_preferences if missing
        cur.execute("SHOW COLUMNS FROM user_preferences LIKE 'active_inventory_id'")
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE user_preferences "
                "ADD COLUMN active_inventory_id INT UNSIGNED DEFAULT NULL"
            )
            conn.commit()

        # 5. Ensure every preferences row has an active inventory
        cur.execute(
            "UPDATE user_preferences SET active_inventory_id = %s "
            "WHERE active_inventory_id IS NULL",
            (default_inv_id,),
        )
        conn.commit()


def init_db():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        cursorclass=pymysql.cursors.DictCursor,
    )
    db_name = os.getenv("DB_NAME", "mealplanner")
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE `{db_name}`")
            for statement in DDL.strip().split(";"):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)
        conn.commit()

        # Migrate existing tables first (adds columns/constraints to pre-existing tables)
        _migrate(conn, db_name)

        # Seed data now that all columns exist
        with conn.cursor() as cur:
            cur.execute(f"USE `{db_name}`")
            cur.execute(
                "INSERT INTO inventories (name) "
                "SELECT 'Default' WHERE NOT EXISTS (SELECT 1 FROM inventories)"
            )
            conn.commit()
            cur.execute("SELECT id FROM inventories ORDER BY id LIMIT 1")
            default_inv_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO user_preferences (vegetarian, active_inventory_id) "
                "SELECT 0, %s WHERE NOT EXISTS (SELECT 1 FROM user_preferences)",
                (default_inv_id,),
            )
        conn.commit()

        print(f"Database '{db_name}' initialised/migrated successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
