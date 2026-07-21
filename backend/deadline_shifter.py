#!/usr/bin/env python3
"""
Advanced Deadline Shifting and Dynamic Rescheduling System
Handles intelligent deadline adjustments based on progress, delays, and external factors
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum
import json

class ShiftReason(Enum):
    """Reasons for deadline shifts"""
    PROGRESS_AHEAD = "progress_ahead"
    PROGRESS_BEHIND = "progress_behind"
    RESOURCE_CONSTRAINT = "resource_constraint"
    EXTERNAL_DELAY = "external_delay"
    PRIORITY_CHANGE = "priority_change"
    SCOPE_CHANGE = "scope_change"
    DEPENDENCY_DELAY = "dependency_delay"
    BUFFER_ADJUSTMENT = "buffer_adjustment"

class DeadlineShifter:
    """Advanced deadline shifting and rescheduling system"""
    
    def __init__(self):
        self.db_path = os.path.abspath("okr.db")
        
    def get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
    
    def is_business_day(self, date: datetime.date) -> bool:
        """Check if a date is a business day (Monday-Friday)"""
        return date.weekday() < 5
    
    def next_business_day(self, date: datetime.date) -> datetime.date:
        """Get the next business day from a given date"""
        next_day = date + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def add_business_days(self, start_date: datetime.date, business_days: int) -> datetime.date:
        """Add business days to a date"""
        current_date = start_date
        remaining_days = business_days
        
        while remaining_days > 0:
            current_date = self.next_business_day(current_date)
            remaining_days -= 1
            
        return current_date
    
    def calculate_progress_drift(self, objective_id: int) -> Dict[str, float]:
        """Calculate how far ahead/behind schedule an objective is"""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        try:
            # Get objective deadline
            cursor.execute("SELECT deadline FROM objectives WHERE id = ?", (objective_id,))
            objective_deadline = cursor.fetchone()
            if not objective_deadline:
                return {"drift": 0.0, "status": "unknown"}
            
            objective_deadline = datetime.strptime(objective_deadline[0], '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # Calculate expected vs actual progress
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as in_progress_tasks
                FROM tasks 
                WHERE objective_id = ?
            """, (objective_id,))
            
            task_stats = cursor.fetchone()
            if not task_stats:
                return {"drift": 0.0, "status": "no_tasks"}
            
            total_tasks, completed_tasks, in_progress_tasks = task_stats
            
            # Calculate expected progress based on time elapsed
            total_days = (objective_deadline - today).days
            if total_days <= 0:
                return {"drift": -1.0, "status": "overdue"}
            
            elapsed_days = (today - (objective_deadline - timedelta(days=total_days))).days
            expected_progress = elapsed_days / total_days if total_days > 0 else 0
            actual_progress = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            # Calculate drift (positive = ahead, negative = behind)
            drift = actual_progress - expected_progress
            
            # Determine status
            if drift >= 0.1:
                status = "ahead"
            elif drift <= -0.1:
                status = "behind"
            else:
                status = "on_track"
            
            return {
                "drift": drift,
                "status": status,
                "expected_progress": expected_progress,
                "actual_progress": actual_progress,
                "elapsed_days": elapsed_days,
                "total_days": total_days
            }
            
        finally:
            conn.close()
    
    def shift_deadlines_for_progress(self, objective_id: int, shift_reason: ShiftReason, 
                                   shift_days: int = 0, auto_calculate: bool = True) -> Dict[str, any]:
        """Shift deadlines based on progress analysis or manual adjustment"""
        
        if auto_calculate:
            # Auto-calculate shift based on progress drift
            drift_analysis = self.calculate_progress_drift(objective_id)
            if drift_analysis["status"] == "ahead":
                shift_days = -max(1, int(abs(drift_analysis["drift"]) * 5))  # Reduce time if ahead
            elif drift_analysis["status"] == "behind":
                shift_days = max(1, int(abs(drift_analysis["drift"]) * 5))   # Add time if behind
        
        conn = self.get_conn()
        cursor = conn.cursor()
        
        try:
            # Get objective details
            cursor.execute("SELECT objective, deadline FROM objectives WHERE id = ?", (objective_id,))
            objective_data = cursor.fetchone()
            if not objective_data:
                return {"success": False, "error": "Objective not found"}
            
            objective_name, current_deadline = objective_data
            current_deadline_date = datetime.strptime(current_deadline, '%Y-%m-%d').date()
            
            # Calculate new deadline
            if shift_days > 0:
                new_deadline = self.add_business_days(current_deadline_date, shift_days)
            else:
                # For negative shifts, go backwards
                temp_date = current_deadline_date
                remaining_days = abs(shift_days)
                while remaining_days > 0:
                    temp_date = temp_date - timedelta(days=1)
                    if self.is_business_day(temp_date):
                        remaining_days -= 1
                new_deadline = temp_date
            
            # Update objective deadline
            cursor.execute("""
                UPDATE objectives 
                SET deadline = ? 
                WHERE id = ?
            """, (new_deadline.strftime('%Y-%m-%d'), objective_id))
            
            # Shift all task deadlines proportionally
            cursor.execute("""
                SELECT id, deadline, weight FROM tasks 
                WHERE objective_id = ? 
                ORDER BY id ASC
            """, (objective_id,))
            
            tasks = cursor.fetchall()
            task_shifts = {}
            
            for task in tasks:
                task_id, task_deadline, weight = task
                if task_deadline:
                    task_date = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                    
                    # Calculate proportional shift based on weight
                    if weight and weight > 0:
                        proportional_shift = int(shift_days * (weight / sum(t[2] for t in tasks if t[2])))
                    else:
                        proportional_shift = shift_days
                    
                    if proportional_shift > 0:
                        new_task_deadline = self.add_business_days(task_date, proportional_shift)
                    else:
                        # Handle negative shifts
                        temp_date = task_date
                        remaining_days = abs(proportional_shift)
                        while remaining_days > 0:
                            temp_date = temp_date - timedelta(days=1)
                            if self.is_business_day(temp_date):
                                remaining_days -= 1
                        new_task_deadline = temp_date
                    
                    # Update task deadline
                    cursor.execute("""
                        UPDATE tasks 
                        SET deadline = ? 
                        WHERE id = ?
                    """, (new_task_deadline.strftime('%Y-%m-%d'), task_id))
                    
                    task_shifts[task_id] = {
                        "old_deadline": task_deadline,
                        "new_deadline": new_task_deadline.strftime('%Y-%m-%d'),
                        "shift_days": proportional_shift
                    }
            
            # Shift subtask deadlines proportionally within their tasks
            for task_id in task_shifts:
                cursor.execute("""
                    SELECT id, deadline, weight FROM subtasks 
                    WHERE task_id = ? 
                    ORDER BY id ASC
                """, (task_id,))
                
                subtasks = cursor.fetchall()
                if subtasks:
                    task_shift = task_shifts[task_id]["shift_days"]
                    
                    for subtask in subtasks:
                        subtask_id, subtask_deadline, weight = subtask
                        if subtask_deadline:
                            subtask_date = datetime.strptime(subtask_deadline, '%Y-%m-%d').date()
                            
                            # Calculate proportional shift for subtask
                            if weight and weight > 0:
                                total_subtask_weight = sum(s[2] for s in subtasks if s[2])
                                proportional_shift = int(task_shift * (weight / total_subtask_weight)) if total_subtask_weight > 0 else task_shift
                            else:
                                proportional_shift = task_shift
                            
                            if proportional_shift > 0:
                                new_subtask_deadline = self.add_business_days(subtask_date, proportional_shift)
                            else:
                                # Handle negative shifts
                                temp_date = subtask_date
                                remaining_days = abs(proportional_shift)
                                while remaining_days > 0:
                                    temp_date = temp_date - timedelta(days=1)
                                    if self.is_business_day(temp_date):
                                        remaining_days -= 1
                                new_subtask_deadline = temp_date
                            
                            # Update subtask deadline
                            cursor.execute("""
                                UPDATE subtasks 
                                SET deadline = ? 
                                WHERE id = ?
                            """, (new_subtask_deadline.strftime('%Y-%m-%d'), subtask_id))
            
            # Log the shift operation
            shift_log = {
                "objective_id": objective_id,
                "shift_reason": shift_reason.value,
                "shift_days": shift_days,
                "old_deadline": current_deadline,
                "new_deadline": new_deadline.strftime('%Y-%m-%d'),
                "task_shifts": task_shifts,
                "timestamp": datetime.now().isoformat(),
                "auto_calculated": auto_calculate
            }
            
            # Store shift log (you can implement a separate table for this)
            self._log_shift_operation(shift_log)
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Successfully shifted deadlines by {shift_days} business days",
                "shift_details": shift_log
            }
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def _log_shift_operation(self, shift_log: Dict[str, any]):
        """Log deadline shift operations for audit trail"""
        # This could be implemented as a separate table in the database
        # For now, we'll just print it
        print(f"🔄 Deadline Shift Log: {json.dumps(shift_log, indent=2)}")
    
    def get_shift_history(self, objective_id: int) -> List[Dict[str, any]]:
        """Get history of deadline shifts for an objective"""
        # This would query a shift_logs table
        # For now, return empty list
        return []
    
    def validate_shift_impact(self, objective_id: int, shift_days: int) -> Dict[str, any]:
        """Validate the impact of a proposed deadline shift"""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        try:
            # Get current deadlines
            cursor.execute("SELECT deadline FROM objectives WHERE id = ?", (objective_id,))
            objective_deadline = cursor.fetchone()
            if not objective_deadline:
                return {"valid": False, "error": "Objective not found"}
            
            current_deadline = datetime.strptime(objective_deadline[0], '%Y-%m-%d').date()
            
            # Calculate new deadline
            if shift_days > 0:
                new_deadline = self.add_business_days(current_deadline, shift_days)
            else:
                # For negative shifts
                temp_date = current_deadline
                remaining_days = abs(shift_days)
                while remaining_days > 0:
                    temp_date = temp_date - timedelta(days=1)
                    if self.is_business_day(temp_date):
                        remaining_days -= 1
                new_deadline = temp_date
            
            # Check if new deadline is in the past
            today = datetime.now().date()
            if new_deadline < today:
                return {
                    "valid": False, 
                    "error": "New deadline would be in the past",
                    "new_deadline": new_deadline.strftime('%Y-%m-%d'),
                    "days_in_past": (today - new_deadline).days
                }
            
            # Check impact on dependencies
            cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE objective_id = ? AND deadline > ?
            """, (objective_id, new_deadline.strftime('%Y-%m-%d')))
            
            tasks_exceeding = cursor.fetchone()[0]
            
            impact_analysis = {
                "valid": True,
                "current_deadline": current_deadline.strftime('%Y-%m-%d'),
                "new_deadline": new_deadline.strftime('%Y-%m-%d'),
                "shift_days": shift_days,
                "business_days_shifted": abs(shift_days),
                "tasks_exceeding_new_deadline": tasks_exceeding,
                "warnings": []
            }
            
            if tasks_exceeding > 0:
                impact_analysis["warnings"].append(f"{tasks_exceeding} tasks would exceed the new deadline")
            
            if shift_days < -10:
                impact_analysis["warnings"].append("Large deadline reduction may impact quality")
            
            if shift_days > 30:
                impact_analysis["warnings"].append("Large deadline extension may indicate scope creep")
            
            return impact_analysis
            
        finally:
            conn.close()
    
    def auto_adjust_for_dependencies(self, objective_id: int) -> Dict[str, any]:
        """Automatically adjust deadlines based on dependency delays"""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        try:
            # Get all tasks and their dependencies
            cursor.execute("""
                SELECT t1.id, t1.task, t1.deadline, t1.weight,
                       t2.id as dep_id, t2.task as dep_task, t2.deadline as dep_deadline
                FROM tasks t1
                LEFT JOIN task_dependencies td ON t1.id = td.task_id
                LEFT JOIN tasks t2 ON td.dependency_id = t2.id
                WHERE t1.objective_id = ?
                ORDER BY t1.id, t2.id
            """, (objective_id,))
            
            dependencies = cursor.fetchall()
            adjustments_needed = []
            
            for dep in dependencies:
                if dep[4]:  # Has dependency
                    task_deadline = datetime.strptime(dep[2], '%Y-%m-%d').date()
                    dep_deadline = datetime.strptime(dep[5], '%Y-%m-%d').date()
                    
                    # Check if dependency deadline is after task deadline
                    if dep_deadline > task_deadline:
                        adjustment_days = (dep_deadline - task_deadline).days
                        adjustments_needed.append({
                            "task_id": dep[0],
                            "task_name": dep[1],
                            "current_deadline": dep[2],
                            "dependency_deadline": dep[5],
                            "adjustment_needed": adjustment_days
                        })
            
            if adjustments_needed:
                # Apply adjustments
                total_adjustment = max(adj["adjustment_needed"] for adj in adjustments_needed)
                result = self.shift_deadlines_for_progress(
                    objective_id, 
                    ShiftReason.DEPENDENCY_DELAY, 
                    total_adjustment, 
                    auto_calculate=False
                )
                
                return {
                    "success": True,
                    "message": f"Adjusted deadlines for {len(adjustments_needed)} dependency conflicts",
                    "adjustments": adjustments_needed,
                    "total_adjustment_days": total_adjustment,
                    "shift_result": result
                }
            else:
                return {
                    "success": True,
                    "message": "No dependency conflicts detected",
                    "adjustments": []
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

# Utility functions for external use
def shift_objective_deadlines(objective_id: int, shift_days: int, reason: str = "manual") -> Dict[str, any]:
    """Utility function to shift objective deadlines"""
    shifter = DeadlineShifter()
    shift_reason = ShiftReason(reason) if reason in [r.value for r in ShiftReason] else ShiftReason.PRIORITY_CHANGE
    
    # Validate shift first
    validation = shifter.validate_shift_impact(objective_id, shift_days)
    if not validation["valid"]:
        return validation
    
    return shifter.shift_deadlines_for_progress(objective_id, shift_reason, shift_days, auto_calculate=False)

def auto_adjust_deadlines(objective_id: int) -> Dict[str, any]:
    """Utility function to automatically adjust deadlines based on progress"""
    shifter = DeadlineShifter()
    return shifter.shift_deadlines_for_progress(objective_id, ShiftReason.PROGRESS_BEHIND, auto_calculate=True)

if __name__ == "__main__":
    # Test the deadline shifter
    print("Testing Deadline Shifter...")
    
    shifter = DeadlineShifter()
    
    # Test with a sample objective
    test_objective_id = 2  # Use existing objective
    
    # Check current progress
    drift = shifter.calculate_progress_drift(test_objective_id)
    print(f"Progress Drift: {drift}")
    
    # Validate a potential shift
    validation = shifter.validate_shift_impact(test_objective_id, 5)
    print(f"Shift Validation: {validation}")
    
    print("Deadline Shifter test completed!")
