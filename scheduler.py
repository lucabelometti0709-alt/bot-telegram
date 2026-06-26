import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from telegram import Bot
from dotenv import load_dotenv
from database import Database

# Carica le variabili d'ambiente
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Configura il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()
        self.scheduler = AsyncIOScheduler()
        self.scheduled_reminders = set()
    
    def start(self):
        """Avvia lo scheduler"""
        # Aggiungi il job per il messaggio giornaliero alle 8:00
        self.scheduler.add_job(
            self.send_daily_message,
            CronTrigger(hour=8, minute=0),
            id='daily_message',
            replace_existing=True
        )
        
        # Avvia lo scheduler
        self.scheduler.start()
        logger.info("Scheduler avviato")
        
        # Carica i promemoria esistenti
        self.load_reminders()
    
    async def send_daily_message(self):
        """Invia il messaggio giornaliero alle 8:00"""
        if not CHAT_ID:
            logger.error("CHAT_ID non configurato")
            return
        
        today = datetime.now().strftime('%Y-%m-%d')
        tasks = self.db.get_tasks_by_date(today)
        
        message = f"🌅 Buongiorno! Ecco cosa devi fare oggi ({today}):\n\n"
        
        if not tasks:
            message += "Nessuna attività programmata per oggi. 🎉"
        else:
            for task in tasks:
                status = "✅" if task['completed'] else "⏳"
                message += f"{status} {task['time']} - {task['description']}\n"
        
        await self.bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"Messaggio giornaliero inviato alle 8:00")
        
        # Ricarica i promemoria per oggi
        self.load_reminders()
    
    def load_reminders(self):
        """Carica i promemoria per tutte le attività future"""
        # Rimuovi tutti i job di promemoria esistenti
        self.remove_all_reminders()
        
        # Carica tutte le attività
        tasks = self.db.get_all_tasks()
        
        for task in tasks:
            if not task['completed']:
                self.schedule_reminder(task)
    
    def schedule_reminder(self, task):
        """Programma un promemoria 5 minuti prima di un'attività"""
        task_datetime = datetime.strptime(f"{task['date']} {task['time']}", '%Y-%m-%d %H:%M')
        reminder_time = task_datetime - timedelta(minutes=5)
        
        # Se il promemoria è nel futuro, programmalo
        if reminder_time > datetime.now():
            job_id = f"reminder_{task['id']}"
            
            self.scheduler.add_job(
                self.send_reminder,
                DateTrigger(run_date=reminder_time),
                args=[task['id']],
                id=job_id,
                replace_existing=True
            )
            
            self.scheduled_reminders.add(job_id)
            logger.info(f"Promemoria programmato per attività {task['id']} alle {reminder_time}")
    
    def remove_all_reminders(self):
        """Rimuove tutti i job di promemoria"""
        for job_id in list(self.scheduled_reminders):
            try:
                self.scheduler.remove_job(job_id)
                self.scheduled_reminders.remove(job_id)
            except Exception as e:
                logger.warning(f"Impossibile rimuovere job {job_id}: {e}")
    
    async def send_reminder(self, task_id):
        """Invia un promemoria 5 minuti prima di un'attività"""
        if not CHAT_ID:
            logger.error("CHAT_ID non configurato")
            return
        
        task = self.db.get_task_by_id(task_id)
        if task and not task['completed']:
            message = f"⏰ Promemoria!\n\nFra 5 minuti devi:\n{task['description']}\n\nOra: {task['time']}"
            await self.bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info(f"Promemoria inviato per attività {task_id}")
        
        # Rimuovi il job dalla lista
        job_id = f"reminder_{task_id}"
        if job_id in self.scheduled_reminders:
            self.scheduled_reminders.remove(job_id)
    
    def refresh_reminders(self):
        """Ricarica tutti i promemoria (chiamato dopo aggiunta/modifica attività)"""
        self.load_reminders()
    
    def shutdown(self):
        """Ferma lo scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler fermato")
