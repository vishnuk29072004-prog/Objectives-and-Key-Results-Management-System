import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict, Any, Optional
import time
import random
from agents import create_reminder_graph
from models import ReminderState


try:
    from llm_config import gemini_llm, qwen_llm, safe_llm_call
    LLM_AVAILABLE = True
except ImportError:
    print("⚠️ LLM configuration not available - using fallback email templates")
    LLM_AVAILABLE = False


SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', '')


llm_call_tracker = {}
last_llm_reset = time.time()

def reset_llm_rate_limits():
    """Reset LLM rate limit tracking every hour"""
    global last_llm_reset, llm_call_tracker
    current_time = time.time()
    if current_time - last_llm_reset > 3600:  
        llm_call_tracker.clear()
        last_llm_reset = current_time
        print("LLM rate limit tracker reset")

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect('okr.db')

def get_due_reminders() -> List[Dict[str, Any]]:
    """
    Get all due reminders from the database
    Returns list of reminder dictionaries
    """
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        
        # Get all objectives to check for overdue subtasks
        cursor.execute("""
            SELECT id, objective, deadline, owner 
            FROM objectives
        """)
        
        objectives = cursor.fetchall()
        reminders = []
        
        for obj in objectives:
            obj_id, objective, deadline, owner = obj
            
            
            cursor.execute("""
                SELECT id, task, deadline 
                FROM tasks 
                WHERE objective_id = ? 
                AND completed = 0
                AND deadline <= date('now', '+7 days')
            """, (obj_id,))
            
            tasks = cursor.fetchall()
            
            
            # Get only subtasks due within 2 days (including overdue)
            cursor.execute("""
                SELECT id, subtask, deadline 
                FROM subtasks 
                WHERE task_id IN (
                    SELECT id FROM tasks WHERE objective_id = ?
                )
                AND completed = 0
                AND deadline IS NOT NULL
                AND deadline <= date('now', '+2 days')
                ORDER BY deadline ASC
            """, (obj_id,))
            
            all_subtasks = cursor.fetchall()
            
            if tasks or all_subtasks:
                
                cleaned_subtasks = []
                for s in all_subtasks:
                    subtask_name = s[1]
                    # Remove numbering like "1 ", "2 ", "3 " from the beginning
                    if subtask_name and len(subtask_name) > 2:
                        # Check if it starts with a number followed by space
                        if subtask_name[0].isdigit() and subtask_name[1] == ' ':
                            subtask_name = subtask_name[2:].strip()
                        # Also check for patterns like "1. ", "2. "
                        elif subtask_name[0].isdigit() and subtask_name[1] == '.' and subtask_name[2] == ' ':
                            subtask_name = subtask_name[3:].strip()
                    
                    cleaned_subtasks.append({
                        'id': s[0], 
                        'name': subtask_name, 
                        'deadline': s[2]
                    })
                
                reminders.append({
                    'objective_id': obj_id,
                    'objective': objective,
                    'deadline': deadline,
                    'owner': owner or RECIPIENT_EMAIL, 
                    'tasks': [{'id': t[0], 'name': t[1], 'deadline': t[2]} for t in tasks],
                    'subtasks': cleaned_subtasks
                })
        
        return reminders
        
    finally:
        conn.close()

# ============================================================================
# LangGraph types/state for modular reminder flow
# ============================================================================



def generate_llm_reminder(reminder: Dict[str, Any]) -> str:
    """
    Generate personalized email content using LLM
    Returns HTML email body
    """
    if not LLM_AVAILABLE:
        return generate_fallback_email(reminder)
    
    
    reset_llm_rate_limits()
    
    
    current_time = time.time()
    if llm_call_tracker.get('reminder_emails', 0) >= 5:
        print("⚠️ LLM rate limit reached for reminder emails - using fallback")
        return generate_fallback_email(reminder)
    
    try:
       
        objective = reminder['objective']
        owner = reminder.get('owner', 'Team Member')
        tasks = reminder.get('tasks', [])
        subtasks = reminder.get('subtasks', [])
        
        
        urgent_subtasks = []
        for subtask in subtasks:
            try:
                deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
                days_until = (deadline_date - datetime.now()).days
                if days_until <= 1:
                    urgent_subtasks.append(subtask)
            except:
                urgent_subtasks.append(subtask)
        
       
        prompt = f"""
        Create a professional, personalized email reminder for OKR goal management. 
        
        Context:
        - Objective: {objective[:200]}...
        - Recipient: {owner}
        - Tasks due: {len(tasks)}
        - Subtasks due: {len(subtasks)}
        - Urgent subtasks (due today/tomorrow): {len(urgent_subtasks)}
        
        Requirements:
        1. Write in a professional but friendly tone
        2. Be specific about what needs to be done
        3. Create urgency without being overwhelming
        4. Include actionable next steps
        5. Format as HTML with proper styling
        6. Keep it concise but comprehensive
        7. Use emojis sparingly but effectively
        
        Task details:
        {chr(10).join([f"- {task['name']} (Due: {task['deadline']})" for task in tasks])}
        
        Subtask details:
        {chr(10).join([f"- {subtask['name']} (Due: {subtask['deadline']})" for subtask in subtasks])}
        
        Generate a complete HTML email body that includes:
        - Professional greeting
        - Clear summary of what's due
        - Specific action items
        - Encouraging closing
        - Professional styling
        """
        
        
        llm_model = gemini_llm if gemini_llm else qwen_llm
        
        if llm_model:
            print(f"🤖 Generating LLM email for objective: {objective[:50]}...")
            response = safe_llm_call(prompt, llm_model, max_retries=2, agent_name="reminder_agent")
            
            
            llm_call_tracker['reminder_emails'] = llm_call_tracker.get('reminder_emails', 0) + 1
            
            
            if response and len(response.strip()) > 100:
               
                if not response.strip().startswith('<html'):
                    response = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                        {response}
                    </body>
                    </html>
                    """
                return response
            else:
                print("⚠️ LLM response too short, using fallback")
                return generate_fallback_email(reminder)
        else:
            print("⚠️ No LLM model available, using fallback")
            return generate_fallback_email(reminder)
            
    except Exception as e:
        print(f"❌ LLM email generation failed: {e}")
        return generate_fallback_email(reminder)

def generate_fallback_email(reminder: Dict[str, Any]) -> str:
    """
    Generate fallback email content when LLM is not available
    """
    objective = reminder['objective']
    owner = reminder.get('owner', 'Team Member')
    tasks = reminder.get('tasks', [])
    subtasks = reminder.get('subtasks', [])
    
    
    urgent_subtasks = []
    for subtask in subtasks:
        try:
            deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
            days_until = (deadline_date - datetime.now()).days
            if days_until <= 1:
                urgent_subtasks.append(subtask)
        except:
            urgent_subtasks.append(subtask)
    
    
    if urgent_subtasks:
        subject = f"🚨 URGENT: {len(urgent_subtasks)} Subtask(s) Due TODAY - {objective[:50]}..."
    elif subtasks:
        subject = f"⚠️ REMINDER: {len(subtasks)} Subtask(s) Due Soon - {objective[:50]}..."
    else:
        subject = f"Reminder: {objective[:50]}... - Deadline Approaching"
    
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d32f2f;">📋 OKR Progress Reminder</h2>
        <div style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0;">
            <p><strong>Objective:</strong> {objective[:100]}...</p>
            <p><strong>Owner:</strong> {owner}</p>
            <p><strong>Priority:</strong> {'HIGH - Immediate attention required' if urgent_subtasks else 'Medium - Action needed soon'}</p>
        </div>
    """
    
    if tasks:
        body += """
        <h3 style="color: #1976d2;">📋 Tasks Due Soon:</h3>
        <ul style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
        """
        for task in tasks:
            body += f"<li style='margin: 8px 0;'><strong>{task['name']}</strong> (Due: {task['deadline']})</li>"
        body += "</ul>"
    
    if subtasks:
        urgency_class = "background-color: #ffebee; border: 2px solid #f44336;" if urgent_subtasks else "background-color: #fff3e0; border: 2px solid #ff9800;"
        body += f"""
        <h3 style="color: #d32f2f; font-size: 18px;">{'🚨 URGENT SUBTASKS - IMMEDIATE ACTION REQUIRED:' if urgent_subtasks else '⚠️ Subtasks Due Soon:'}</h3>
        <div style="{urgency_class} padding: 20px; border-radius: 8px; margin: 20px 0;">
        """
        for subtask in subtasks:
            try:
                deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
                days_until = (deadline_date - datetime.now()).days
                if days_until == 0:
                    urgency = "🚨 DUE TODAY"
                    urgency_color = "#d32f2f"
                    background_color = "#ffcdd2"
                elif days_until == 1:
                    urgency = "🚨 DUE TOMORROW"
                    urgency_color = "#d32f2f"
                    background_color = "#ffcdd2"
                else:
                    urgency = f"⚠️ DUE IN {days_until} DAYS"
                    urgency_color = "#f57c00"
                    background_color = "#ffe0b2"
                
                body += f"""
                <div style="background-color: {background_color}; padding: 12px; margin: 10px 0; border-radius: 5px; border-left: 4px solid {urgency_color};">
                    <div style="font-weight: bold; color: {urgency_color}; margin-bottom: 5px;">{urgency}</div>
                    <div style="font-size: 16px; margin-bottom: 5px;"><strong>{subtask['name']}</strong></div>
                    <div style="color: #666; font-size: 14px;">Deadline: {subtask['deadline']}</div>
                </div>
                """
            except:
                body += f"""
                <div style="background-color: #ffcdd2; padding: 12px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #f44336;">
                    <div style="font-weight: bold; color: #d32f2f; margin-bottom: 5px;">⚠️ URGENT</div>
                    <div style="font-size: 16px; margin-bottom: 5px;"><strong>{subtask['name']}</strong></div>
                    <div style="color: #666; font-size: 14px;">Deadline: {subtask['deadline']}</div>
                </div>
                """
        body += "</div>"
    
    body += """
        <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin-top: 20px; border: 2px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-top: 0;">🎯 Action Required:</h4>
            <ul style="color: #2e7d32; margin: 10px 0;">
                <li><strong>Complete the above tasks and subtasks as soon as possible</strong></li>
                <li><strong>Update your progress in the OKR management system</strong></li>
                <li><strong>Mark items as completed when finished</strong></li>
                <li><strong>Contact your team lead if you need assistance</strong></li>
            </ul>
            <p style="color: #2e7d32; font-weight: bold; margin: 15px 0 0 0;">⏰ Please prioritize these items!</p>
        </div>
    </div>
    </body>
    </html>
    """
    
    return body

def send_email_reminder(
    reminder: Dict[str, Any],
    prebuilt_body: Optional[str] = None,
    prebuilt_subject: Optional[str] = None,
) -> bool:
    """
    Send email reminder for a specific objective/task
    Returns True if email sent successfully, False otherwise
    """
    try:
        
        if os.getenv('DISABLE_EMAIL', 'false').lower() == 'true':
            print(f"']\=-8765t4r3e2w1q' disabled - would send reminder for objective: {reminder['objective']}")
            return True
        
       
        smtp_server = SMTP_SERVER
        smtp_port = SMTP_PORT
        email_user = EMAIL_ADDRESS
        email_password = EMAIL_PASSWORD
        
        if not email_user or not email_password:
            print("Email credentials not configured - skipping email reminder")
            return False
        
        
        print(f"Preparing to send email reminder for objective: {reminder['objective']}")
        print(f"Tasks due: {len(reminder.get('tasks', []))}")
        print(f"Subtasks due: {len(reminder.get('subtasks', []))}")
        
        
        if not reminder.get('tasks') and not reminder.get('subtasks'):
            print("No tasks or subtasks due - skipping email")
            return False
    
        def is_valid_email(value: str) -> bool:
            if not value or not isinstance(value, str):
                return False
            import re
            return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", value) is not None

        raw_owner = reminder.get('owner')
        to_email = raw_owner if is_valid_email(raw_owner) else RECIPIENT_EMAIL
        if not is_valid_email(to_email):
            print(f"Owner '{raw_owner}' is not a valid email. Falling back to configured RECIPIENT_EMAIL.")
            return False

        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = to_email 

        if prebuilt_subject:
            msg['Subject'] = prebuilt_subject
        else:
            if reminder.get('subtasks'):
                urgent_subtasks = [s for s in reminder['subtasks'] if s['deadline'] == datetime.now().strftime('%Y-%m-%d')]
                if urgent_subtasks:
                    msg['Subject'] = f"🚨 URGENT: {len(urgent_subtasks)} Subtask(s) Due TODAY - {reminder['objective'][:50]}..."
                else:
                    msg['Subject'] = f"⚠️ REMINDER: {len(reminder['subtasks'])} Subtask(s) Due Soon - {reminder['objective'][:50]}..."
            else:
                msg['Subject'] = f"Reminder: {reminder['objective'][:50]}... - Deadline Approaching"
        
        body = prebuilt_body if prebuilt_body else generate_llm_reminder(reminder)
        msg.attach(MIMEText(body, 'html'))
        
        print(f"📧 Sending email to: {msg['To']}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email reminder sent successfully for objective: {reminder['objective']}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email reminder: {e}")
        return False



def check_and_send_reminders():
    """
    Check for due reminders and send them
    This function is called by the scheduler
    """
    print(f"🔍 Checking for due reminders at {datetime.now()}")
    
    reminders = get_due_reminders()
    
    if not reminders:
        print("✅ No due reminders found")
        return
    
    print(f"📧 Found {len(reminders)} reminders to send")
    
    
    try:
        reminder_graph = create_reminder_graph()
    except Exception as e:
        print(f"❌ Failed to create reminder graph: {e}")
        reminder_graph = None

    emails_sent = 0
    for reminder in reminders:
        print(f"📤 Processing reminder for objective: {reminder['objective']}")
        print(f"   Tasks due: {len(reminder.get('tasks', []))}")
        print(f"   Subtasks due: {len(reminder.get('subtasks', []))}")

        if reminder_graph is None:
            if send_email_reminder(reminder):
                emails_sent += 1
                print(f"✅ Email sent successfully for objective: {reminder['objective']}")
            else:
                print(f"❌ Failed to send email for objective: {reminder['objective']}")
            continue
        initial_state: ReminderState = {"reminder": reminder}
        try:
            final_state = reminder_graph.invoke(initial_state)
            if final_state.get("send_success"):
                emails_sent += 1
        except Exception as e:
            print(f"❌ Reminder flow failed: {e}")
    
    print(f"📊 Reminder check completed: {emails_sent}/{len(reminders)} emails sent")
    return {"emails_sent": emails_sent, "total": len(reminders)}

def manual_reminder_check():
    """
    Manual reminder check function that can be called via API
    """
    print(f"Manual reminder check triggered at {datetime.now()}")
    summary = check_and_send_reminders()
    return {"status": "reminder_check_completed", "timestamp": datetime.now().isoformat(), **summary}

def preview_email_content():
    """
    Preview email content without sending
    """
    print("📧 PREVIEWING EMAIL CONTENT:")
    print("=" * 60)
    
    reminders = get_due_reminders()
    
    for i, reminder in enumerate(reminders, 1):
        print(f"\n📧 EMAIL {i}:")
        print(f"To: {reminder.get('owner', RECIPIENT_EMAIL)}")
        
        
        if reminder.get('subtasks'):
            urgent_subtasks = [s for s in reminder['subtasks'] if s['deadline'] == datetime.now().strftime('%Y-%m-%d')]
            if urgent_subtasks:
                subject = f"🚨 URGENT: {len(urgent_subtasks)} Subtask(s) Due TODAY - {reminder['objective'][:50]}..."
            else:
                subject = f"⚠️ REMINDER: {len(reminder['subtasks'])} Subtask(s) Due Soon - {reminder['objective'][:50]}..."
        else:
            subject = f"Reminder: {reminder['objective'][:50]}... - Deadline Approaching"
        
        print(f"Subject: {subject}")
        print(f"\nContent Preview:")
        print(f"Objective: {reminder['objective'][:100]}...")
        print(f"Owner: {reminder.get('owner', RECIPIENT_EMAIL)}")
        
        if reminder.get('subtasks'):
            print(f"\n🚨 URGENT SUBTASKS:")
            for subtask in reminder['subtasks']:
                try:
                    deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
                    days_until = (deadline_date - datetime.now()).days
                    if days_until == 0:
                        urgency = "🚨 DUE TODAY"
                    elif days_until == 1:
                        urgency = "🚨 DUE TOMORROW"
                    else:
                        urgency = f"⚠️ DUE IN {days_until} DAYS"
                    print(f"  {urgency}: {subtask['name']} (Deadline: {subtask['deadline']})")
                except:
                    print(f"  ⚠️ URGENT: {subtask['name']} (Deadline: {subtask['deadline']})")
        
        print(f"\n🎯 ACTION REQUIRED:")
        print(f"  - Complete the above subtasks as soon as possible")
        print(f"  - Update your progress in the OKR management system")
        print(f"  - Mark subtasks as completed when finished")
        print(f"  - Contact your team lead if you need assistance")
        print("=" * 60)

def log_reminder_check():
    """
    Log reminder check activity
    """
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminder_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reminders_found INTEGER,
                emails_sent INTEGER
            )
        """)
        
        reminders = get_due_reminders()
        emails_sent = sum(1 for r in reminders if send_email_reminder(r))
        
        cursor.execute("""
            INSERT INTO reminder_logs (reminders_found, emails_sent)
            VALUES (?, ?)
        """, (len(reminders), emails_sent))
        
        conn.commit()
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 Testing reminder agent...")
    print("=" * 50)
    
    reminders = get_due_reminders()
    print(f"📋 Found {len(reminders)} due reminders")
    
    for i, reminder in enumerate(reminders, 1):
        print(f"\n📌 Reminder {i}:")
        print(f"   Objective: {reminder['objective']}")
        print(f"   Deadline: {reminder['deadline']}")
        print(f"   Owner: {reminder.get('owner', RECIPIENT_EMAIL)}")
        print(f"   Tasks due: {len(reminder.get('tasks', []))}")
        print(f"   Subtasks due: {len(reminder.get('subtasks', []))}")
        
        if reminder.get('tasks'):
            print("   📋 Tasks:")
            for task in reminder['tasks']:
                print(f"      - {task['name']} (Due: {task['deadline']})")
        
        if reminder.get('subtasks'):
            print("   ⚠️ Subtasks:")
            for subtask in reminder['subtasks']:
                print(f"      - {subtask['name']} (Due: {subtask['deadline']})")
        print("-" * 30)
    
    print("\n📧 PREVIEWING EMAIL CONTENT:")
    preview_email_content()
    
    print("\n🚀 Running full reminder check...")
    check_and_send_reminders()
    print("✅ Test completed!")
