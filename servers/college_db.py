import sqlite3
import csv
import os
from mcp.server.fastmcp import FastMCP
from contextlib import contextmanager
import json

# Initialize FastMCP server
mcp = FastMCP("CollegeDatabase")

# Database setup
# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "college.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

def init_db():
    # Only init if db doesn't exist or is empty to avoid overwriting on every restart
    # But for this task, we want to force load the data.
    
    with sqlite3.connect(DB_PATH) as conn:
        # Enable FK support
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Reset schema for this demo
        conn.execute("DROP TABLE IF EXISTS marks")
        conn.execute("DROP TABLE IF EXISTS students")
        conn.execute("DROP TABLE IF EXISTS subjects")
        conn.execute("DROP TABLE IF EXISTS teachers")

        # Create Tables
        conn.execute("""
            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                dob TEXT,
                address TEXT,
                contact TEXT,
                email TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE subjects (
                subject_id INTEGER PRIMARY KEY,
                subject_name TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE teachers (
                teacher_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                dob TEXT,
                address TEXT,
                contact TEXT,
                email TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE marks (
                mark_id INTEGER PRIMARY KEY,
                student_id INTEGER,
                subject_id INTEGER,
                teacher_id INTEGER,
                mark_obtained INTEGER,
                exam_date TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(subject_id) REFERENCES subjects(subject_id),
                FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id)
            )
        """)
        
        # Import Data
        print("Importing data from CSVs...")
        
        # Import Students
        with open(os.path.join(DATA_DIR, "Students.csv"), "r") as f:
            reader = csv.DictReader(f)
            to_db = [(i['StudentID'], i['FirstName'], i['LastName'], i['DateOfBirth'], i['Address'], i['ContactNumber'], i['Email']) for i in reader]
            conn.executemany("INSERT INTO students (student_id, first_name, last_name, dob, address, contact, email) VALUES (?, ?, ?, ?, ?, ?, ?)", to_db)

        # Import Subjects
        with open(os.path.join(DATA_DIR, "Subjects.csv"), "r") as f:
            reader = csv.DictReader(f)
            to_db = [(i['SubjectID'], i['SubjectName']) for i in reader]
            conn.executemany("INSERT INTO subjects (subject_id, subject_name) VALUES (?, ?)", to_db)

        # Import Teachers
        with open(os.path.join(DATA_DIR, "Teachers.csv"), "r") as f:
            reader = csv.DictReader(f)
            to_db = [(i['TeacherID'], i['FirstName'], i['LastName'], i['DateOfBirth'], i['Address'], i['ContactNumber'], i['Email']) for i in reader]
            conn.executemany("INSERT INTO teachers (teacher_id, first_name, last_name, dob, address, contact, email) VALUES (?, ?, ?, ?, ?, ?, ?)", to_db)

        # Import Marks
        with open(os.path.join(DATA_DIR, "Marks.csv"), "r") as f:
            reader = csv.DictReader(f)
            to_db = [(i['MarkID'], i['StudentID'], i['SubjectID'], i['TeacherID'], i['MarkObtained'], i['ExamDate']) for i in reader]
            conn.executemany("INSERT INTO marks (mark_id, student_id, subject_id, teacher_id, mark_obtained, exam_date) VALUES (?, ?, ?, ?, ?, ?)", to_db)
            
        print("Data import complete.")

# Initialize on import
init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@mcp.tool()
def query_marks(student_name: str) -> str:
    """Get marks for a student by their name (first or last)."""
    with get_db() as conn:
        query = """
            SELECT s.first_name, s.last_name, subj.subject_name, m.mark_obtained, m.exam_date
            FROM marks m
            JOIN students s ON m.student_id = s.student_id
            JOIN subjects subj ON m.subject_id = subj.subject_id
            WHERE s.first_name LIKE ? OR s.last_name LIKE ?
        """
        search_term = f"%{student_name}%"
        results = conn.execute(query, (search_term, search_term)).fetchall()
        
        if not results:
            return f"No marks found for student matching '{student_name}'"
            
        return json.dumps([dict(r) for r in results], indent=2)

@mcp.tool()
def get_student_report(student_id: int) -> str:
    """Generate a full report card for a student ID."""
    with get_db() as conn:
        # Get student info
        student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
        if not student:
            return "Student not found"
            
        # Get marks
        marks = conn.execute("""
            SELECT subj.subject_name, m.mark_obtained, t.first_name || ' ' || t.last_name as teacher
            FROM marks m
            JOIN subjects subj ON m.subject_id = subj.subject_id
            JOIN teachers t ON m.teacher_id = t.teacher_id
            WHERE m.student_id = ?
        """, (student_id,)).fetchall()
        
        report = {
            "student": f"{student['first_name']} {student['last_name']}",
            "email": student['email'],
            "results": [dict(m) for m in marks],
            "average_mark": sum(m['mark_obtained'] for m in marks) / len(marks) if marks else 0
        }
        return json.dumps(report, indent=2)

@mcp.tool()
def get_teacher_stats(teacher_name: str) -> str:
    """Analyze performance of students taught by a specific teacher."""
    with get_db() as conn:
        teacher = conn.execute("SELECT teacher_id, first_name, last_name FROM teachers WHERE first_name LIKE ? OR last_name LIKE ?", (f"%{teacher_name}%", f"%{teacher_name}%")).fetchone()
        if not teacher:
            return "Teacher not found"
            
        marks = conn.execute("""
            SELECT m.mark_obtained, s.subject_name 
            FROM marks m
            JOIN subjects s ON m.subject_id = s.subject_id
            WHERE m.teacher_id = ?
        """, (teacher['teacher_id'],)).fetchall()
        
        if not marks:
            return "No marks found for this teacher"
            
        values = [m['mark_obtained'] for m in marks]
        stats = {
            "teacher": f"{teacher['first_name']} {teacher['last_name']}",
            "subjects_taught": list(set(m['subject_name'] for m in marks)),
            "students_graded": len(values),
            "average_student_mark": round(sum(values) / len(values), 2),
            "highest_mark_given": max(values),
            "lowest_mark_given": min(values)
        }
        return json.dumps(stats, indent=2)

@mcp.tool()
def get_top_students(limit: int = 5) -> str:
    """Get the top performing students based on average marks."""
    with get_db() as conn:
        query = """
            SELECT s.first_name, s.last_name, AVG(m.mark_obtained) as avg_mark
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            GROUP BY s.student_id
            ORDER BY avg_mark DESC
            LIMIT ?
        """
        results = conn.execute(query, (limit,)).fetchall()
        return json.dumps([{"student": f"{r['first_name']} {r['last_name']}", "average": round(r['avg_mark'], 2)} for r in results], indent=2)

@mcp.tool()
def update_student_mark(student_id: int, subject_id: int, new_mark: int) -> str:
    """Update a specific mark for a student."""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE marks 
            SET mark_obtained = ? 
            WHERE student_id = ? AND subject_id = ?
        """, (new_mark, student_id, subject_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return "Mark record not found to update."
        return f"Mark updated to {new_mark} for student {student_id} in subject {subject_id}."

@mcp.tool()
def add_new_student(first_name: str, last_name: str, email: str) -> str:
    """Register a new student."""
    with get_db() as conn:
        try:
            cursor = conn.execute("INSERT INTO students (first_name, last_name, email) VALUES (?, ?, ?)", (first_name, last_name, email))
            conn.commit()
            return f"Student added with ID {cursor.lastrowid}"
        except sqlite3.Error as e:
            return f"Database error: {str(e)}"

@mcp.resource("college://students")
def list_students() -> str:
    """List all registered students"""
    with get_db() as conn:
        students = conn.execute("SELECT * FROM students").fetchall()
        return json.dumps([dict(s) for s in students], indent=2)

@mcp.resource("college://teachers")
def list_teachers() -> str:
    """List all teachers"""
    with get_db() as conn:
        teachers = conn.execute("SELECT * FROM teachers").fetchall()
        return json.dumps([dict(t) for t in teachers], indent=2)

@mcp.resource("college://subjects")
def list_subjects() -> str:
    """List all subjects"""
    with get_db() as conn:
        subjects = conn.execute("SELECT * FROM subjects").fetchall()
        return json.dumps([dict(s) for s in subjects], indent=2)

@mcp.tool()
def get_subject_stats(subject_name: str) -> str:
    """Get statistics for a specific subject."""
    with get_db() as conn:
        # Find subject ID
        subject = conn.execute("SELECT subject_id, subject_name FROM subjects WHERE subject_name LIKE ?", (f"%{subject_name}%",)).fetchone()
        if not subject:
            return "Subject not found"
            
        marks = conn.execute("SELECT mark_obtained FROM marks WHERE subject_id = ?", (subject['subject_id'],)).fetchall()
        if not marks:
            return f"No marks recorded for {subject['subject_name']}"
            
        values = [m['mark_obtained'] for m in marks]
        stats = {
            "subject": subject['subject_name'],
            "total_students": len(values),
            "average_mark": sum(values) / len(values),
            "highest_mark": max(values),
            "lowest_mark": min(values)
        }
        return json.dumps(stats, indent=2)

if __name__ == "__main__":
    mcp.run()
