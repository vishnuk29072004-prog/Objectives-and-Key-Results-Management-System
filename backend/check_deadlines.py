#!/usr/bin/env python3
"""
Check existing objectives and their deadline generation
Verify that deadlines are realistic and properly bounded
"""

import sqlite3
from datetime import datetime, timedelta

def check_existing_deadlines():
    """Check existing objectives and their deadline structure"""
    print("🔍 Checking Existing Objectives and Deadlines")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('okr.db')
        cursor = conn.cursor()
        
        # Get all objectives
        cursor.execute("SELECT id, objective, deadline FROM objectives ORDER BY id")
        objectives = cursor.fetchall()
        
        print(f"📋 Found {len(objectives)} objectives in database")
        print()
        
        for obj in objectives:
            objective_id, objective_text, objective_deadline = obj
            
            print(f"🎯 Objective ID: {objective_id}")
            print(f"   Text: {objective_text[:80]}...")
            print(f"   Deadline: {objective_deadline}")
            
            # Get tasks for this objective
            cursor.execute("SELECT id, task, deadline FROM tasks WHERE objective_id = ? ORDER BY id", (objective_id,))
            tasks = cursor.fetchall()
            
            print(f"   📋 Tasks: {len(tasks)}")
            
            for task in tasks:
                task_id, task_name, task_deadline = task
                print(f"      Task: {task_name[:50]}...")
                print(f"        Deadline: {task_deadline}")
                
                # Get subtasks for this task
                cursor.execute("SELECT id, subtask, deadline FROM subtasks WHERE task_id = ? ORDER BY id", (task_id,))
                subtasks = cursor.fetchall()
                
                print(f"        📝 Subtasks: {len(subtasks)}")
                
                for subtask in subtasks:
                    subtask_id, subtask_name, subtask_deadline = subtask
                    print(f"          - {subtask_name[:40]}...")
                    print(f"            Deadline: {subtask_deadline}")
                    
                    # Check if subtask deadline is within task boundary
                    if task_deadline and subtask_deadline:
                        try:
                            task_date = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                            subtask_date = datetime.strptime(subtask_deadline, '%Y-%m-%d').date()
                            
                            if subtask_date > task_date:
                                print(f"            ⚠️  BOUNDARY VIOLATION: Subtask deadline exceeds task deadline!")
                            elif subtask_date < task_date:
                                print(f"            ✅ Boundary respected: Subtask within task timeframe")
                            else:
                                print(f"            ✅ Boundary respected: Subtask deadline matches task deadline")
                        except ValueError:
                            print(f"            ❌ Invalid date format")
                    else:
                        print(f"            ℹ️  No deadline set")
                
                print()
            print("-" * 60)
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking deadlines: {e}")
        import traceback
        traceback.print_exc()

def check_deadline_realism():
    """Check if deadlines are realistic (business days, reasonable durations)"""
    print("\n🔍 Checking Deadline Realism")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('okr.db')
        cursor = conn.cursor()
        
        # Get a sample objective with tasks and subtasks
        cursor.execute("""
            SELECT o.id, o.objective, o.deadline, t.id, t.task, t.deadline, s.id, s.subtask, s.deadline
            FROM objectives o
            JOIN tasks t ON o.id = t.objective_id
            LEFT JOIN subtasks s ON t.id = s.task_id
            WHERE o.id = 1
            ORDER BY t.id, s.id
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("ℹ️  No data found for analysis")
            return
        
        objective_id, objective_text, objective_deadline = results[0][:3]
        
        print(f"🎯 Analyzing Objective: {objective_text[:60]}...")
        print(f"📅 Objective Deadline: {objective_deadline}")
        print()
        
        # Parse objective deadline
        try:
            obj_deadline = datetime.strptime(objective_deadline, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # Calculate business days from today to objective deadline
            business_days = 0
            current_date = today
            while current_date <= obj_deadline:
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    business_days += 1
                current_date += timedelta(days=1)
            
            print(f"📊 Business Days Analysis:")
            print(f"   Today: {today}")
            print(f"   Objective Deadline: {obj_deadline}")
            print(f"   Total Business Days Available: {business_days}")
            print(f"   Calendar Days: {(obj_deadline - today).days + 1}")
            print()
            
            # Analyze task distribution
            current_task = None
            task_count = 0
            subtask_count = 0
            
            for row in results:
                task_id, task_name, task_deadline = row[3:6]
                
                if current_task != task_id:
                    current_task = task_id
                    task_count += 1
                    
                    if task_deadline:
                        try:
                            task_date = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                            task_business_days = 0
                            temp_date = today
                            while temp_date <= task_date:
                                if temp_date.weekday() < 5:
                                    task_business_days += 1
                                temp_date += timedelta(days=1)
                            
                            print(f"📋 Task {task_count}: {task_name[:40]}...")
                            print(f"   Deadline: {task_deadline}")
                            print(f"   Business Days from Today: {task_business_days}")
                            
                            # Check if task deadline is reasonable
                            if task_business_days > business_days:
                                print(f"   ⚠️  TASK DEADLINE EXCEEDS OBJECTIVE DEADLINE!")
                            elif task_business_days <= 0:
                                print(f"   ⚠️  TASK DEADLINE IS IN THE PAST!")
                            else:
                                print(f"   ✅ Task deadline is within objective timeframe")
                            
                        except ValueError:
                            print(f"   ❌ Invalid task deadline format")
                    
                    print()
                
                # Check subtask
                subtask_id, subtask_name, subtask_deadline = row[6:9]
                if subtask_id:
                    subtask_count += 1
                    
                    if subtask_deadline:
                        try:
                            subtask_date = datetime.strptime(subtask_deadline, '%Y-%m-%d').date()
                            subtask_business_days = 0
                            temp_date = today
                            while temp_date <= subtask_date:
                                if temp_date.weekday() < 5:
                                    subtask_business_days += 1
                                temp_date += timedelta(days=1)
                            
                            print(f"   📝 Subtask: {subtask_name[:35]}...")
                            print(f"      Deadline: {subtask_deadline}")
                            print(f"      Business Days from Today: {subtask_business_days}")
                            
                            # Check subtask boundary
                            if task_deadline:
                                try:
                                    task_date = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                                    if subtask_date > task_date:
                                        print(f"      ⚠️  BOUNDARY VIOLATION: Subtask exceeds task deadline!")
                                    elif subtask_date < today:
                                        print(f"      ⚠️  SUBTASK DEADLINE IS IN THE PAST!")
                                    else:
                                        print(f"      ✅ Subtask deadline is valid")
                                except ValueError:
                                    print(f"      ❌ Invalid task deadline for comparison")
                            
                        except ValueError:
                            print(f"      ❌ Invalid subtask deadline format")
                    
                    print()
            
            print(f"📊 Summary:")
            print(f"   Total Tasks: {task_count}")
            print(f"   Total Subtasks: {subtask_count}")
            print(f"   Business Days Available: {business_days}")
            
            # Assess realism
            if business_days > 0:
                avg_days_per_task = business_days / max(1, task_count)
                print(f"   Average Business Days per Task: {avg_days_per_task:.1f}")
                
                if avg_days_per_task >= 2:
                    print("   ✅ Deadline distribution appears realistic")
                else:
                    print("   ⚠️  Deadline distribution may be too aggressive")
            
        except ValueError as e:
            print(f"❌ Error parsing dates: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking deadline realism: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all deadline checks"""
    print("🚀 Deadline Generation Validation Check")
    print("=" * 60)
    
    # Check 1: Basic deadline structure
    check_existing_deadlines()
    
    # Check 2: Deadline realism
    check_deadline_realism()
    
    print("\n" + "=" * 60)
    print("🏁 Deadline validation check completed!")

if __name__ == "__main__":
    main()



