import sqlite3
import random
from datetime import datetime, timedelta

# DB 생성
conn = sqlite3.connect("data/mes_sample.db")
cur = conn.cursor()

# ── 테이블 생성 ────────────────────────────

# 생산 실적
cur.execute("""
CREATE TABLE IF NOT EXISTS production_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date TEXT,
    line_name TEXT,
    product_code TEXT,
    target_qty INTEGER,
    actual_qty INTEGER,
    created_at TEXT
)
""")

# 불량 이력
cur.execute("""
CREATE TABLE IF NOT EXISTS defect_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date TEXT,
    line_name TEXT,
    lot_number TEXT,
    defect_type TEXT,
    defect_qty INTEGER,
    created_at TEXT
)
""")

# 설비 현황
cur.execute("""
CREATE TABLE IF NOT EXISTS equipment_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date TEXT,
    equipment_name TEXT,
    line_name TEXT,
    operation_time INTEGER,
    downtime INTEGER,
    downtime_reason TEXT,
    created_at TEXT
)
""")

# ── 샘플 데이터 삽입 ───────────────────────

lines = ["A라인", "B라인", "C라인"]
products = ["P-001", "P-002", "P-003"]
defect_types = ["치수 불량", "표면 스크래치", "조립 불량", "도장 불량"]
equipments = ["1호기", "2호기", "3호기", "4호기"]
downtime_reasons = ["계획 보전", "고장", "재료 부족", "품질 검사"]

# 최근 3개월치 데이터 생성
base_date = datetime.today()

for i in range(90):
    work_date = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")

    # 생산 실적
    for line in lines:
        target = random.randint(1800, 2200)
        # B라인은 불량 많고 생산량 약간 낮게
        rate = 0.88 if line == "B라인" else random.uniform(0.90, 0.98)
        actual = int(target * rate)
        cur.execute("""
            INSERT INTO production_result (work_date, line_name, product_code, target_qty, actual_qty, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (work_date, line, random.choice(products), target, actual, datetime.now().isoformat()))

    # 불량 이력
    for line in lines:
        # B라인 불량 더 많이
        defect_count = random.randint(5, 12) if line == "B라인" else random.randint(1, 5)
        for j in range(defect_count):
            lot = f"LOT-{work_date.replace('-','')}-{line[0]}{j+1:02d}"
            cur.execute("""
                INSERT INTO defect_log (work_date, line_name, lot_number, defect_type, defect_qty, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (work_date, line, lot, random.choice(defect_types), random.randint(1, 5), datetime.now().isoformat()))

    # 설비 현황
    for eq in equipments:
        line = random.choice(lines)
        op_time = random.randint(380, 480)
        downtime = random.randint(0, 60)
        cur.execute("""
            INSERT INTO equipment_status (work_date, equipment_name, line_name, operation_time, downtime, downtime_reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (work_date, eq, line, op_time, downtime, random.choice(downtime_reasons), datetime.now().isoformat()))

conn.commit()
conn.close()
print("샘플 DB 생성 완료! → data/mes_sample.db")