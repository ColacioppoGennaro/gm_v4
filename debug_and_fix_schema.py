#!/usr/bin/env python3
"""
Auto-fix script per verificare schema database e aggiustare codice
"""

import pymysql
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config

def check_database_schema():
    """Check actual database schema"""
    print("🔍 Connecting to database...")
    
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASS,
            database=Config.DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Connected to database: {Config.DB_NAME}")
        
        with connection.cursor() as cursor:
            # Get events table structure
            print("\n📋 EVENTS TABLE STRUCTURE:")
            print("-" * 80)
            cursor.execute("DESCRIBE events")
            events_columns = cursor.fetchall()
            
            column_names = []
            for col in events_columns:
                print(f"  {col['Field']:30} {col['Type']:20} {col['Null']:5} {col['Key']:5}")
                column_names.append(col['Field'])
            
            print("\n" + "=" * 80)
            
            # Check what we're using in code vs what exists
            code_expects = [
                'start_time', 'end_time', 'created_at', 'updated_at', 
                'deleted_at', 'user_id', 'title', 'description', 
                'location', 'category_id', 'is_all_day', 'recurrence_rule',
                'reminder_minutes', 'color'
            ]
            
            print("\n🔎 COLUMN MAPPING CHECK:")
            print("-" * 80)
            
            mapping = {}
            missing = []
            
            for expected in code_expects:
                if expected in column_names:
                    print(f"  ✅ {expected:30} EXISTS")
                    mapping[expected] = expected
                else:
                    # Try to find similar column
                    found = False
                    for actual in column_names:
                        if expected.replace('_', '') in actual.replace('_', ''):
                            print(f"  ⚠️  {expected:30} -> FOUND AS: {actual}")
                            mapping[expected] = actual
                            found = True
                            break
                    
                    if not found:
                        print(f"  ❌ {expected:30} NOT FOUND")
                        missing.append(expected)
            
            print("\n" + "=" * 80)
            
            if missing:
                print(f"\n❌ MISSING COLUMNS: {', '.join(missing)}")
                print("\n💡 SOLUTION: Run the database schema.sql file again!")
                return None
            
            # Check if any mapping needed
            needs_fix = any(k != v for k, v in mapping.items())
            
            if needs_fix:
                print("\n⚠️  COLUMN NAME MISMATCH DETECTED!")
                print("\nMAPPING NEEDED:")
                for expected, actual in mapping.items():
                    if expected != actual:
                        print(f"  {expected} -> {actual}")
                
                return mapping
            else:
                print("\n✅ ALL COLUMN NAMES MATCH! Schema is correct.")
                print("\n🤔 The error might be elsewhere. Let me check the INSERT query...")
                
                # Show actual INSERT that's failing
                print("\n📝 Checking events.py INSERT query...")
                return "all_good"
        
        connection.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def check_insert_query():
    """Check the actual INSERT query in events.py"""
    print("\n" + "=" * 80)
    print("📝 CHECKING INSERT QUERY IN events.py:")
    print("-" * 80)
    
    events_file = 'backend/modules/routes/events.py'
    
    with open(events_file, 'r') as f:
        content = f.read()
        
    # Find INSERT query
    import re
    insert_match = re.search(r'INSERT INTO events \((.*?)\)', content, re.DOTALL)
    
    if insert_match:
        columns = insert_match.group(1)
        columns_clean = [c.strip() for c in columns.split(',')]
        
        print("\nColumns in INSERT query:")
        for i, col in enumerate(columns_clean, 1):
            print(f"  {i}. {col}")
        
        print(f"\nTotal columns in INSERT: {len(columns_clean)}")
        
        # Check VALUES
        values_match = re.search(r'VALUES \((.*?)\)', content[insert_match.end():])
        if values_match:
            placeholders = values_match.group(1).count('%s')
            print(f"Total placeholders (%s) in VALUES: {placeholders}")
            
            if len(columns_clean) != placeholders:
                print(f"\n❌ MISMATCH! Columns: {len(columns_clean)}, Placeholders: {placeholders}")
            else:
                print(f"\n✅ Columns and placeholders match!")
    
    print("=" * 80)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🔧 SmartLife Organizer - Database Schema Auto-Fix")
    print("=" * 80 + "\n")
    
    result = check_database_schema()
    
    if result == "all_good":
        check_insert_query()
        print("\n💡 If columns match but still errors, the issue is in the SQL query syntax.")
        print("   Run this on the server to see the full error:")
        print("   tail -50 ~/logs/gruppogea.net-*.log | grep -A 10 'Error creating event'")
    elif result:
        print("\n🔧 Column mapping created. Would need to update code with these mappings.")
        print("   (Not implemented in this version - manual fix needed)")
    else:
        print("\n❌ Could not connect to database or schema has issues.")
    
    print("\n" + "=" * 80)
