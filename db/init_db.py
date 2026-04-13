"""
Run this script once to create all tables:
    uv run python -m db.init_db
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DDL = """
CREATE TABLE IF NOT EXISTS inventory (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    item_name    VARCHAR(255) NOT NULL UNIQUE,
    quantity     DECIMAL(10, 3) NOT NULL DEFAULT 0,
    unit         VARCHAR(50)  NOT NULL DEFAULT '',
    category     VARCHAR(100),
    expires_at   DATE,
    added_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP
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
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vegetarian  TINYINT(1)   NOT NULL DEFAULT 0
);
"""


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
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute(f"USE `{db_name}`")
            for statement in DDL.strip().split(";"):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)
            # Seed a single preferences row if none exists
            cur.execute(
                "INSERT INTO user_preferences (vegetarian) "
                "SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM user_preferences)"
            )
        conn.commit()
        print(f"Database '{db_name}' and all tables created successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
