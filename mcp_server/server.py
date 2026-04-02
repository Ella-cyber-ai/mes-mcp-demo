import sqlite3
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# MCP 서버 초기화
mcp = FastMCP("MES Demo Server")

DB_PATH = "data/mes_sample.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Tool 1: 생산 실적 조회 ─────────────────

@mcp.tool()
def get_production(work_date: str = "", line_name: str = "") -> str:
    """생산 실적을 조회합니다. work_date: 날짜(YYYY-MM-DD), line_name: 라인명"""
    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM production_result WHERE 1=1"
    params = []

    if work_date and work_date.strip() and work_date != "null" and work_date != "None":
        query += " AND work_date = ?"
        params.append(work_date)
    if line_name and line_name.strip() and line_name != "null" and line_name != "None":
        query += " AND line_name = ?"
        params.append(line_name)

    query += " ORDER BY work_date DESC LIMIT 20"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "조회된 데이터가 없습니다."

    result = "=== 생산 실적 조회 결과 ===\n"
    for row in rows:
        rate = round(row["actual_qty"] / row["target_qty"] * 100, 1)
        result += f"날짜: {row['work_date']} | 라인: {row['line_name']} | 목표: {row['target_qty']} | 실적: {row['actual_qty']} | 달성률: {rate}%\n"
    return result

# ── Tool 2: 불량률 분석 ────────────────────

@mcp.tool()
@mcp.tool()
def get_defect_analysis(year_month: str = "", line_name: str = "") -> str:
    """불량률을 분석합니다. year_month: 연월(YYYY-MM), line_name: 라인명"""
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT 
            line_name,
            COUNT(*) as defect_count,
            SUM(defect_qty) as total_defect_qty,
            defect_type
        FROM defect_log
        WHERE 1=1
    """
    params = []

    if year_month and year_month.strip() and year_month not in ("null", "None", ""):
        query += " AND work_date LIKE ?"
        params.append(f"{year_month}%")
    if line_name and line_name.strip() and line_name not in ("null", "None", ""):
        query += " AND line_name = ?"
        params.append(line_name)

    query += " GROUP BY line_name, defect_type ORDER BY total_defect_qty DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "조회된 데이터가 없습니다."

    result = "=== 불량 분석 결과 ===\n"
    for row in rows:
        result += f"라인: {row['line_name']} | 불량유형: {row['defect_type']} | 건수: {row['defect_count']} | 불량수량: {row['total_defect_qty']}\n"
    return result

# ── Tool 3: 설비 가동률 조회 ───────────────

@mcp.tool()
def get_equipment_status(work_date: str = None, line_name: str = None) -> str:
    """설비 가동률을 조회합니다. work_date: 날짜(YYYY-MM-DD), line_name: 라인명"""
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT 
            equipment_name,
            line_name,
            operation_time,
            downtime,
            downtime_reason,
            work_date
        FROM equipment_status
        WHERE 1=1
    """
    params = []

    if work_date:
        query += " AND work_date = ?"
        params.append(work_date)
    if line_name:
        query += " AND line_name = ?"
        params.append(line_name)

    query += " ORDER BY work_date DESC LIMIT 20"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "조회된 데이터가 없습니다."

    result = "=== 설비 가동률 조회 결과 ===\n"
    for row in rows:
        rate = round((row["operation_time"] - row["downtime"]) / row["operation_time"] * 100, 1)
        result += f"날짜: {row['work_date']} | 설비: {row['equipment_name']} | 라인: {row['line_name']} | 가동률: {rate}% | 비가동사유: {row['downtime_reason']}\n"
    return result

# ── Tool 4: 일일 보고서 생성 ───────────────

@mcp.tool()
def get_daily_report(work_date: str="") -> str:
    """일일 생산 보고서를 생성합니다. work_date: 날짜(YYYY-MM-DD)"""
    conn = get_db()
    cur = conn.cursor()

    # 생산 실적
    cur.execute("""
        SELECT line_name, target_qty, actual_qty
        FROM production_result
        WHERE work_date = ?
        ORDER BY line_name
    """, (work_date,))
    prod_rows = cur.fetchall()

    # 불량 현황
    cur.execute("""
        SELECT line_name, COUNT(*) as cnt, SUM(defect_qty) as qty
        FROM defect_log
        WHERE work_date = ?
        GROUP BY line_name
    """, (work_date,))
    defect_rows = cur.fetchall()

    conn.close()

    if not prod_rows:
        return f"{work_date} 데이터가 없습니다."

    report = f"=== 일일 생산 보고서 ({work_date}) ===\n\n"
    report += "[생산 실적]\n"
    for row in prod_rows:
        rate = round(row["actual_qty"] / row["target_qty"] * 100, 1)
        report += f"  {row['line_name']}: 목표 {row['target_qty']} / 실적 {row['actual_qty']} / 달성률 {rate}%\n"

    report += "\n[불량 현황]\n"
    for row in defect_rows:
        report += f"  {row['line_name']}: {row['cnt']}건 / 불량수량 {row['qty']}개\n"

    return report

# ── 서버 실행 ──────────────────────────────

if __name__ == "__main__":
    print("MES MCP Server 시작!")
    mcp.run()