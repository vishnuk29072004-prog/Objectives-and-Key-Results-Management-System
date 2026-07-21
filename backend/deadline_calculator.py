import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import random

class DeadlineCalculator:
    def __init__(self):
        self.db_path = os.path.abspath("okr.db")
        
    def get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
    
    def is_business_day(self, date: datetime.date) -> bool:
        """Check if a date is a business day (Monday-Friday)"""
        return date.weekday() < 5  # Monday = 0, Friday = 4
    
    def next_business_day(self, date: datetime.date) -> datetime.date:
        """Get the next business day from a given date"""
        next_day = date + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def add_business_days(self, start_date: datetime.date, business_days: int) -> datetime.date:
        """Add a specific number of business days to a start date"""
        current_date = start_date
        remaining_days = business_days
        
        while remaining_days > 0:
            current_date = self.next_business_day(current_date)
            remaining_days -= 1
            
        return current_date
    
    def business_days_between(self, start_date: datetime.date, end_date: datetime.date) -> int:
        """Calculate the number of business days between two dates"""
        if start_date > end_date:
            return 0
            
        business_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_business_day(current_date):
                business_days += 1
            current_date += timedelta(days=1)
            
        return business_days
    
    def calculate_task_complexity(self, task_description: str) -> float:
        """
        Calculate task complexity score (1-10) based on description analysis
        """
        complexity_score = 1.0
        
        # Keywords that indicate complexity
        complexity_keywords = {
            'research': 2.0,
            'analysis': 2.5,
            'development': 3.0,
            'testing': 2.0,
            'documentation': 1.5,
            'review': 1.0,
            'planning': 1.5,
            'coordination': 2.0,
            'implementation': 3.0,
            'deployment': 2.5,
            'optimization': 2.0,
            'integration': 3.0,
            'migration': 3.5,
            'audit': 2.0,
            'strategy': 2.5,
            'campaign': 2.0,
            'content': 1.5,
            'design': 2.0,
            'prototype': 2.5,
            'pilot': 2.0
        }
        
        # Count complexity keywords
        task_lower = task_description.lower()
        for keyword, score in complexity_keywords.items():
            if keyword in task_lower:
                complexity_score += score
        
        # Additional complexity factors
        if any(word in task_lower for word in ['multiple', 'several', 'various', 'comprehensive']):
            complexity_score += 1.5
        if any(word in task_lower for word in ['technical', 'advanced', 'complex', 'sophisticated']):
            complexity_score += 2.0
        if any(word in task_lower for word in ['urgent', 'critical', 'priority', 'high-impact']):
            complexity_score += 1.0
            
        # Cap complexity at 10
        return min(complexity_score, 10.0)
    
    def calculate_subtask_complexity(self, subtask_description: str) -> float:
        """
        Calculate subtask complexity score (1-5) based on description
        """
        complexity_score = 1.0
        
        # Subtask-specific complexity indicators
        subtask_keywords = {
            'identify': 1.5,
            'analyze': 2.0,
            'research': 1.5,
            'document': 1.0,
            'create': 1.5,
            'develop': 2.0,
            'test': 1.5,
            'review': 1.0,
            'implement': 2.0,
            'deploy': 1.5,
            'optimize': 1.5,
            'integrate': 2.0,
            'configure': 1.5,
            'schedule': 1.0,
            'secure': 1.5,
            'launch': 1.5,
            'monitor': 1.0,
            'generate': 1.5,
            'conduct': 1.5,
            'prepare': 1.0
        }
        
        subtask_lower = subtask_description.lower()
        for keyword, score in subtask_keywords.items():
            if keyword in subtask_lower:
                complexity_score += score
        
        # Cap complexity at 5
        return min(complexity_score, 5.0)
    
    def estimate_duration(self, complexity: float, task_type: str = 'task') -> int:
        """
        Estimate duration in business days based on complexity and task type
        """
        if task_type == 'task':
            # Tasks: 2-15 business days based on complexity
            base_days = max(2, int(complexity * 1.5))
            # Add some randomness for realistic variation
            variation = random.uniform(0.8, 1.3)
            return max(2, int(base_days * variation))
        else:
            # Subtasks: 1-4 business days based on complexity
            base_days = max(1, int(complexity * 0.8))
            variation = random.uniform(0.8, 1.2)
            return max(1, int(base_days * variation))
    
    def calculate_dependencies(self, task_id: int, task_order: List[int]) -> List[int]:
        """
        Get list of task IDs that this task depends on based on task order and complexity
        """
        try:
            # Find the position of current task in the order
            current_index = task_order.index(task_id)
            
            # Dependencies are all tasks that come before this one
            # In a production system, you might have explicit dependency relationships
            dependencies = task_order[:current_index]
            
            # Limit dependencies to avoid circular dependencies
            return dependencies[-2:] if len(dependencies) > 2 else dependencies
        except ValueError:
            # Task not found in order, no dependencies
            return []
    
    def calculate_realistic_deadlines(self, objective_id: int) -> Dict[str, List[Dict]]:
        """
        Calculate realistic deadlines for all tasks and subtasks in an objective
        with proper boundary enforcement and business day awareness
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        
        try:
            # Get objective deadline
            cursor.execute("SELECT deadline FROM objectives WHERE id = ?", (objective_id,))
            objective_deadline = cursor.fetchone()
            if not objective_deadline:
                return {}
            
            objective_deadline = datetime.strptime(objective_deadline[0], '%Y-%m-%d').date()
            
            # Get all tasks for this objective
            cursor.execute("""
                SELECT id, task, deadline, weight 
                FROM tasks 
                WHERE objective_id = ? 
                ORDER BY id ASC
            """, (objective_id,))
            
            tasks = cursor.fetchall()
            
            # Calculate task deadlines with proper dependency management and business day awareness
            task_deadlines = []
            current_date = datetime.now().date()
            
            # Ensure we start on a business day
            if not self.is_business_day(current_date):
                current_date = self.next_business_day(current_date)
            
            task_order = [task[0] for task in tasks]  # List of task IDs in order
            
            for task in tasks:
                task_id, task_name, existing_deadline, weight = task
                
                # Calculate complexity and duration
                complexity = self.calculate_task_complexity(task_name)
                duration_business_days = self.estimate_duration(complexity, 'task')
                
                # Calculate start date (considering dependencies)
                dependencies = self.calculate_dependencies(task_id, task_order)
                if dependencies:
                    # Start after the latest dependency completes
                    latest_dependency_end = current_date
                    for dep_id in dependencies:
                        dep_task = next((t for t in task_deadlines if t['id'] == dep_id), None)
                        if dep_task:
                            dep_end = datetime.strptime(dep_task['deadline'], '%Y-%m-%d').date()
                            latest_dependency_end = max(latest_dependency_end, dep_end)
                    start_date = self.next_business_day(latest_dependency_end)
                else:
                    start_date = current_date
                
                # Calculate end date using business days
                end_date = self.add_business_days(start_date, duration_business_days - 1)  # -1 because start day counts
                
                # Ensure deadline doesn't exceed objective deadline
                if end_date > objective_deadline:
                    end_date = objective_deadline
                    # Recalculate start date to fit within objective deadline
                    required_business_days = duration_business_days
                    temp_end = end_date
                    temp_start = temp_end
                    for _ in range(required_business_days - 1):
                        temp_start = temp_start - timedelta(days=1)
                        while not self.is_business_day(temp_start):
                            temp_start = temp_start - timedelta(days=1)
                    start_date = temp_start
                
                task_deadlines.append({
                    'id': task_id,
                    'name': task_name,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'deadline': end_date.strftime('%Y-%m-%d'),
                    'complexity': complexity,
                    'duration': duration_business_days,
                    'weight': weight or 1.0
                })
                
                # Update current date for next task (next business day after this task ends)
                current_date = self.next_business_day(end_date)
            
            # Calculate subtask deadlines with strict boundary enforcement
            subtask_deadlines = []
            
            for task in task_deadlines:
                task_id = task['id']
                task_start = datetime.strptime(task['start_date'], '%Y-%m-%d').date()
                task_end = datetime.strptime(task['deadline'], '%Y-%m-%d').date()
                
                # Get subtasks for this task
                cursor.execute("""
                    SELECT id, subtask, deadline, weight 
                    FROM subtasks 
                    WHERE task_id = ? 
                    ORDER BY id ASC
                """, (task_id,))
                
                subtasks = cursor.fetchall()
                
                if subtasks:
                    subtask_count = len(subtasks)
                    
                    if subtask_count == 1:
                        # Single subtask gets the full task duration
                        subtask_deadlines.append({
                            'id': subtasks[0][0],
                            'name': subtasks[0][1],
                            'task_id': task_id,
                            'start_date': task_start.strftime('%Y-%m-%d'),
                            'deadline': task_end.strftime('%Y-%m-%d'),
                            'complexity': self.calculate_subtask_complexity(subtasks[0][1]),
                            'duration': self.business_days_between(task_start, task_end) + 1,
                            'weight': subtasks[0][3] or 1.0
                        })
                    else:
                        # Multiple subtasks - distribute time proportionally with strict boundary enforcement
                        # Calculate total complexity for proportional distribution
                        total_complexity = sum(self.calculate_subtask_complexity(st[1]) for st in subtasks)
                        
                        # Calculate available business days for subtasks
                        available_business_days = self.business_days_between(task_start, task_end) + 1
                        
                        # Reserve some buffer time between subtasks (1 business day)
                        buffer_days = subtask_count - 1
                        working_days = max(1, available_business_days - buffer_days)
                        
                        current_subtask_start = task_start
                        remaining_working_days = working_days
                        
                        for i, subtask in enumerate(subtasks):
                            subtask_id, subtask_name, existing_deadline, weight = subtask
                            
                            # Calculate proportional duration based on complexity
                            if i == subtask_count - 1:
                                # Last subtask gets remaining time
                                subtask_duration = remaining_working_days
                            else:
                                # Proportional duration based on complexity
                                complexity = self.calculate_subtask_complexity(subtask_name)
                                proportional_days = max(1, int(working_days * (complexity / total_complexity)))
                                subtask_duration = min(proportional_days, remaining_working_days)
                                remaining_working_days -= subtask_duration
                            
                            # Calculate subtask end date
                            subtask_end = self.add_business_days(current_subtask_start, subtask_duration - 1)
                            
                            # CRITICAL: Ensure subtask doesn't exceed task boundary
                            if subtask_end > task_end:
                                subtask_end = task_end
                                # Recalculate duration to fit within task boundary
                                subtask_duration = self.business_days_between(current_subtask_start, subtask_end) + 1
                            
                            # CRITICAL: Ensure subtask doesn't start before task
                            if current_subtask_start < task_start:
                                current_subtask_start = task_start
                                # Recalculate duration to fit within task boundary
                                subtask_duration = self.business_days_between(current_subtask_start, subtask_end) + 1
                            
                            subtask_deadlines.append({
                                'id': subtask_id,
                                'name': subtask_name,
                                'task_id': task_id,
                                'start_date': current_subtask_start.strftime('%Y-%m-%d'),
                                'deadline': subtask_end.strftime('%Y-%m-%d'),
                                'complexity': self.calculate_subtask_complexity(subtask_name),
                                'duration': subtask_duration,
                                'weight': weight or 1.0
                            })
                            
                            # Move to next subtask start (next business day after this subtask ends)
                            current_subtask_start = self.next_business_day(subtask_end)
            
            # Validate deadline alignment
            self._validate_deadline_alignment(task_deadlines, subtask_deadlines)
            
            return {
                'tasks': task_deadlines,
                'subtasks': subtask_deadlines
            }
            
        finally:
            conn.close()
    
    def _validate_deadline_alignment(self, task_deadlines: List[Dict], subtask_deadlines: List[Dict]) -> None:
        """
        Validate that all subtask deadlines are within their parent task boundaries
        """
        task_boundaries = {task['id']: {
            'start': datetime.strptime(task['start_date'], '%Y-%m-%d').date(),
            'end': datetime.strptime(task['deadline'], '%Y-%m-%d').date()
        } for task in task_deadlines}
        
        validation_errors = []
        
        for subtask in subtask_deadlines:
            task_id = subtask['task_id']
            if task_id not in task_boundaries:
                validation_errors.append(f"Subtask {subtask['name']} references non-existent task {task_id}")
                continue
            
            task_start = task_boundaries[task_id]['start']
            task_end = task_boundaries[task_id]['end']
            subtask_start = datetime.strptime(subtask['start_date'], '%Y-%m-%d').date()
            subtask_end = datetime.strptime(subtask['deadline'], '%Y-%m-%d').date()
            
            # Check boundaries
            if subtask_start < task_start:
                validation_errors.append(f"Subtask {subtask['name']} starts before task {task_id}")
            if subtask_end > task_end:
                validation_errors.append(f"Subtask {subtask['name']} ends after task {task_id}")
            if subtask_start > subtask_end:
                validation_errors.append(f"Subtask {subtask['name']} has invalid start/end dates")
        
        if validation_errors:
            error_msg = "Deadline validation failed:\n" + "\n".join(validation_errors)
            print(f"⚠️ {error_msg}")
            raise ValueError(error_msg)
        else:
            print("✅ All deadline alignments validated successfully")
    
    def update_database_deadlines(self, objective_id: int) -> bool:
        """
        Update the database with calculated realistic deadlines
        """
        try:
            deadlines = self.calculate_realistic_deadlines(objective_id)
            
            print(f"Calculated deadlines for objective {objective_id}:")
            print(f"  Tasks: {len(deadlines.get('tasks', []))}")
            print(f"  Subtasks: {len(deadlines.get('subtasks', []))}")
            
            if not deadlines or (not deadlines.get('tasks') and not deadlines.get('subtasks')):
                print(f"No deadlines calculated for objective {objective_id}")
                return False
            
            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Update task deadlines
            for task in deadlines['tasks']:
                print(f"  Updating task {task['id']}: {task['deadline']}")
                cursor.execute("""
                    UPDATE tasks 
                    SET deadline = ? 
                    WHERE id = ?
                """, (task['deadline'], task['id']))
            
            # Update subtask deadlines
            for subtask in deadlines['subtasks']:
                print(f"  Updating subtask {subtask['id']}: {subtask['deadline']}")
                cursor.execute("""
                    UPDATE subtasks 
                    SET deadline = ? 
                    WHERE id = ?
                """, (subtask['deadline'], subtask['id']))
            
            conn.commit()
            conn.close()
            
            print(f"Successfully updated deadlines for objective {objective_id}")
            return True
            
        except Exception as e:
            print(f"Error updating deadlines: {e}")
            return False

# Utility function to recalculate all deadlines
def recalculate_all_deadlines():
    """
    Recalculate deadlines for all objectives in the database
    """
    calculator = DeadlineCalculator()
    conn = calculator.get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM objectives")
        objective_ids = [row[0] for row in cursor.fetchall()]
        
        updated_count = 0
        for obj_id in objective_ids:
            if calculator.update_database_deadlines(obj_id):
                updated_count += 1
        
        print(f"Updated deadlines for {updated_count} objectives")
        return updated_count
        
    finally:
        conn.close()

if __name__ == "__main__":
    # Test the deadline calculator
    print("Testing Deadline Calculator...")
    recalculate_all_deadlines()
