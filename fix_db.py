import sqlite3
import os

session_path = "sessions/main.session"

if os.path.exists(session_path):
    try:
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()
        
        # Check if username column exists
        cursor.execute("PRAGMA table_info(peers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "username" not in columns:
            print("[INFO] Adding 'username' column to 'peers' table...")
            cursor.execute("ALTER TABLE peers ADD COLUMN username TEXT")
            conn.commit()
            print("[SUCCESS] Column added successfully.")
        else:
            print("[INFO] Column 'username' already exists.")
            
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to fix database: {e}")
else:
    print(f"[ERROR] Session file not found at {session_path}")
