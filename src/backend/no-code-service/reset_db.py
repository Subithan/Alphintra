#!/usr/bin/env python3
"""
Reset database schema
"""

import psycopg2
import time
import sys

def reset_database():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to connect to database...")
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                database="alphintra",
                user="alphintra",
                password="alphintra"
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            print("Dropping existing schema...")
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
            
            print("Creating new schema...")
            cur.execute("CREATE SCHEMA public")
            cur.execute("GRANT ALL ON SCHEMA public TO alphintra")
            cur.execute("GRANT ALL ON SCHEMA public TO public")
            
            print("✅ Database schema reset successfully!")
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Waiting 2 seconds before retry...")
                time.sleep(2)
            else:
                print("❌ All attempts failed")
                return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)