import schedule
import time
import threading
from datetime import datetime, timedelta
import os
import sys


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from remainder_agent import check_and_send_reminders, get_due_reminders, send_email_reminder

class ReminderScheduler:
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the reminder scheduler"""
        if self.is_running:
            print("⚠️ Scheduler is already running")
            return
        
        print("🚀 Starting Reminder Scheduler...")
        print("=" * 50)
        
        
        schedule.every().day.at("09:00").do(self.daily_morning_reminder)
        print("📅 Scheduled daily morning reminder at 9:00 AM")
        
        
        schedule.every().day.at("10:00").do(self.business_hour_check)
        schedule.every().day.at("14:00").do(self.business_hour_check)
        schedule.every().day.at("16:00").do(self.business_hour_check)
        print("📅 Scheduled business hour checks at 10:00 AM, 2:00 PM, and 4:00 PM")
        
        
        schedule.every().day.at("17:00").do(self.end_of_day_summary)
        print("📅 Scheduled end-of-day summary at 5:00 PM")
        
        self.is_running = True
        
        
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("✅ Reminder scheduler started successfully!")
        print("📊 Scheduler will run in the background")
        print("🛑 To stop the scheduler, call stop_scheduler()")
        
    def stop_scheduler(self):
        """Stop the reminder scheduler"""
        if not self.is_running:
            print("⚠️ Scheduler is not running")
            return
        
        print("🛑 Stopping Reminder Scheduler...")
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        print("✅ Reminder scheduler stopped")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                print("🛑 Scheduler interrupted by user")
                break
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def daily_morning_reminder(self):
        """Send daily morning reminder with all due items"""
        print(f"🌅 Daily Morning Reminder Check - {datetime.now()}")
        print("=" * 50)
        
        try:
            
            reminders = get_due_reminders()
            
            if not reminders:
                print("✅ No due reminders for today - great job!")
                return
            
            print(f"📧 Found {len(reminders)} objectives with due items")
            self._send_morning_summary_email(reminders)
            check_and_send_reminders()
            
        except Exception as e:
            print(f"❌ Daily morning reminder failed: {e}")
    
    def business_hour_check(self):
        """Periodic check during business hours"""
        current_time = datetime.now()
        print(f"⏰ Business Hour Check - {current_time.strftime('%H:%M')}")
        
        try:
            
            reminders = get_due_reminders()
            
            urgent_reminders = []
            for reminder in reminders:
                urgent_subtasks = []
                for subtask in reminder.get('subtasks', []):
                    try:
                        deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
                        days_until = (deadline_date - current_time).days
                        if days_until <= 1: 
                            urgent_subtasks.append(subtask)
                    except:
                        urgent_subtasks.append(subtask)
                
                if urgent_subtasks:
                    urgent_reminders.append(reminder)
            
            if urgent_reminders:
                print(f"🚨 Found {len(urgent_reminders)} objectives with urgent items")
                check_and_send_reminders()
            else:
                print("✅ No urgent items found")
                
        except Exception as e:
            print(f"❌ Business hour check failed: {e}")
    
    def end_of_day_summary(self):
        """Send end-of-day summary"""
        print(f"🌆 End of Day Summary - {datetime.now()}")
        print("=" * 50)
        
        try:
            reminders = get_due_reminders()
            
            if not reminders:
                print("✅ No pending items for tomorrow")
                return
            
            print(f"📊 End of day summary: {len(reminders)} objectives with pending items")
            
            
            self._send_eod_summary_email(reminders)
            
        except Exception as e:
            print(f"❌ End of day summary failed: {e}")
    
    def _send_morning_summary_email(self, reminders):
        """Send comprehensive morning summary email"""
        try:
            from remainder_agent import EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL, SMTP_SERVER, SMTP_PORT
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = RECIPIENT_EMAIL
            msg['Subject'] = f"🌅 Daily OKR Morning Briefing - {datetime.now().strftime('%Y-%m-%d')}"
            
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976d2;">🌅 Good Morning! Here's Your OKR Daily Briefing</h2>
                <p style="color: #666; font-size: 14px;">Date: {datetime.now().strftime('%A, %B %d, %Y')}</p>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1565c0; margin-top: 0;">📊 Today's Overview</h3>
                    <p><strong>Total Objectives with Due Items:</strong> {len(reminders)}</p>
                    <p><strong>Total Tasks Due:</strong> {sum(len(r.get('tasks', [])) for r in reminders)}</p>
                    <p><strong>Total Subtasks Due:</strong> {sum(len(r.get('subtasks', [])) for r in reminders)}</p>
                </div>
            """
            
            
            for i, reminder in enumerate(reminders, 1):
                objective = reminder['objective']
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
                
                urgency_color = "#d32f2f" if urgent_subtasks else "#1976d2"
                urgency_bg = "#ffebee" if urgent_subtasks else "#e3f2fd"
                
                body += f"""
                <div style="background-color: {urgency_bg}; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid {urgency_color};">
                    <h4 style="color: {urgency_color}; margin-top: 0;">Objective {i}: {objective[:80]}...</h4>
                    <p><strong>Owner:</strong> {reminder.get('owner', 'Not specified')}</p>
                    <p><strong>Deadline:</strong> {reminder['deadline']}</p>
                """
                
                if tasks:
                    body += "<p><strong>Tasks Due:</strong></p><ul>"
                    for task in tasks:
                        body += f"<li>{task['name']} (Due: {task['deadline']})</li>"
                    body += "</ul>"
                
                if subtasks:
                    body += "<p><strong>Subtasks Due:</strong></p><ul>"
                    for subtask in subtasks:
                        try:
                            deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
                            days_until = (deadline_date - datetime.now()).days
                            if days_until == 0:
                                urgency_icon = "🚨"
                            elif days_until == 1:
                                urgency_icon = "⚠️"
                            else:
                                urgency_icon = "📋"
                        except:
                            urgency_icon = "📋"
                        body += f"<li>{urgency_icon} {subtask['name']} (Due: {subtask['deadline']})</li>"
                    body += "</ul>"
                
                body += "</div>"
            
            body += """
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin-top: 20px; border: 2px solid #4caf50;">
                    <h4 style="color: #2e7d32; margin-top: 0;">🎯 Today's Action Plan</h4>
                    <ul style="color: #2e7d32;">
                        <li><strong>Review all due items above</strong></li>
                        <li><strong>Prioritize urgent subtasks (due today/tomorrow)</strong></li>
                        <li><strong>Update progress in the OKR system</strong></li>
                        <li><strong>Mark completed items</strong></li>
                        <li><strong>Reach out for help if needed</strong></li>
                    </ul>
                    <p style="color: #2e7d32; font-weight: bold;">Have a productive day! 🚀</p>
                </div>
            </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print("✅ Morning summary email sent successfully")
            
        except Exception as e:
            print(f"❌ Failed to send morning summary email: {e}")
    
    def _send_eod_summary_email(self, reminders):
        """Send end-of-day summary email"""
        try:
            from remainder_agent import EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL, SMTP_SERVER, SMTP_PORT
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = RECIPIENT_EMAIL
            msg['Subject'] = f"🌆 End of Day OKR Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
           
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976d2;">🌆 End of Day OKR Summary</h2>
                <p style="color: #666; font-size: 14px;">Date: {datetime.now().strftime('%A, %B %d, %Y')}</p>
                
                <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #f57c00; margin-top: 0;">📊 Tomorrow's Preview</h3>
                    <p><strong>Objectives with Pending Items:</strong> {len(reminders)}</p>
                    <p><strong>Tasks to Complete:</strong> {sum(len(r.get('tasks', [])) for r in reminders)}</p>
                    <p><strong>Subtasks to Complete:</strong> {sum(len(r.get('subtasks', [])) for r in reminders)}</p>
                </div>
            """
            
            
            for i, reminder in enumerate(reminders, 1):
                objective = reminder['objective']
                tasks = reminder.get('tasks', [])
                subtasks = reminder.get('subtasks', [])
                
                body += f"""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h4 style="color: #424242; margin-top: 0;">Objective {i}: {objective[:80]}...</h4>
                    <p><strong>Owner:</strong> {reminder.get('owner', 'Not specified')}</p>
                    <p><strong>Deadline:</strong> {reminder['deadline']}</p>
                """
                
                if tasks:
                    body += "<p><strong>Pending Tasks:</strong></p><ul>"
                    for task in tasks:
                        body += f"<li>{task['name']} (Due: {task['deadline']})</li>"
                    body += "</ul>"
                
                if subtasks:
                    body += "<p><strong>Pending Subtasks:</strong></p><ul>"
                    for subtask in subtasks:
                        body += f"<li>{subtask['name']} (Due: {subtask['deadline']})</li>"
                    body += "</ul>"
                
                body += "</div>"
            
            body += """
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin-top: 20px; border: 2px solid #4caf50;">
                    <h4 style="color: #2e7d32; margin-top: 0;">🌙 End of Day Checklist</h4>
                    <ul style="color: #2e7d32;">
                        <li><strong>Review today's progress</strong></li>
                        <li><strong>Update any completed items</strong></li>
                        <li><strong>Plan tomorrow's priorities</strong></li>
                        <li><strong>Prepare for upcoming deadlines</strong></li>
                    </ul>
                    <p style="color: #2e7d32; font-weight: bold;">Great work today! Rest well and see you tomorrow! 🌙</p>
                </div>
            </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print("✅ End of day summary email sent successfully")
            
        except Exception as e:
            print(f"❌ Failed to send end of day summary email: {e}")
    
    def manual_check(self):
        """Manual reminder check"""
        print(f"🔍 Manual Reminder Check - {datetime.now()}")
        check_and_send_reminders()
    
    def get_scheduler_status(self):
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "next_run": schedule.next_run(),
            "jobs": len(schedule.jobs)
        }


scheduler = ReminderScheduler()

def start_reminder_scheduler():
    """Start the reminder scheduler"""
    scheduler.start_scheduler()

def stop_reminder_scheduler():
    """Stop the reminder scheduler"""
    scheduler.stop_scheduler()

def manual_reminder_check():
    """Manual reminder check"""
    scheduler.manual_check()

def get_scheduler_status():
    """Get scheduler status"""
    return scheduler.get_scheduler_status()

if __name__ == "__main__":
    print("🧪 Testing Reminder Scheduler...")
    print("=" * 50)
    
    # Test manual check
    print("🔍 Testing manual reminder check...")
    manual_reminder_check()
    
    # Test scheduler
    print("\n🚀 Testing scheduler...")
    start_reminder_scheduler()
    
    try:
       
        print("⏰ Scheduler running for 5 minutes...")
        time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
    finally:
        stop_reminder_scheduler()
    
    print("✅ Scheduler test completed!") 