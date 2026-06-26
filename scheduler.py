import os
import logging
import threading
import time
from datetime import datetime, timedelta
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
        self.running = False
        self.thread = None
        self.reminders = {}  # {task_id: reminder_time}
    
    def start(self):
        """Avvia lo scheduler in un thread separato"""
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler avviato")
        
        # Carica i promemoria esistenti
        self.load_reminders()
    
    def _run_scheduler(self):
        """Loop principale dello scheduler"""
        last_daily_check = None
        
        while self.running:
            try:
                now = datetime.now()
                
                # Controlla se è ora del messaggio giornaliero (8:00)
                if now.hour == 8 and now.minute == 0:
                    if last_daily_check != now.date():
                        self.send_daily_message()
                        last_daily_check = now.date()
                
                # Controlla i promemoria
                self.check_reminders(now)
                
                # Dormi 10 secondi
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Errore nello scheduler: {e}")
                time.sleep(10)
    
    def send_daily_message(self):
        """Invia il messaggio giornaliero alle 8:00"""
        if not CHAT_ID:
            logger.error("CHAT_ID non configurato")
            return
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            tasks = self.db.get_tasks_by_date(today)
            
            message = f"🌅 Buongiorno! Ecco cosa devi fare oggi ({today}):\n\n"
            
            if not tasks:
                message += "Nessuna attività programmata per oggi. 🎉"
            else:
                for task in tasks:
                    status = "✅" if task['completed'] else "⏳"
                    message += f"{status} {task['time']} - {task['description']}\n"
            
            # Usa un thread per inviare il messaggio (operazione async in thread sync)
            threading.Thread(target=self._send_message_sync, args=(message,)).start()
            logger.info(f"Messaggio giornaliero inviato alle 8:00")
            
            # Ricarica i promemoria per oggi
            self.load_reminders()
            
        except Exception as e:
            logger.error(f"Errore invio messaggio giornaliero: {e}")
    
    def _send_message_sync(self, message):
        """Invia messaggio in modo sincrono"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.bot.send_message(chat_id=CHAT_ID, text=message))
            loop.close()
        except Exception as e:
            logger.error(f"Errore invio messaggio: {e}")
    
    def load_reminders(self):
        """Carica i promemoria per tutte le attività future"""
        self.reminders.clear()
        
        # Carica tutte le attività
        tasks = self.db.get_all_tasks()
        
        for task in tasks:
            if not task['completed']:
                self.schedule_reminder(task)
    
    def schedule_reminder(self, task):
        """Programma un promemoria 5 minuti prima di un'attività"""
        try:
            task_datetime = datetime.strptime(f"{task['date']} {task['time']}", '%Y-%m-%d %H:%M')
            reminder_time = task_datetime - timedelta(minutes=5)
            
            # Se il promemoria è nel futuro, salvalo
            if reminder_time > datetime.now():
                self.reminders[task['id']] = reminder_time
                logger.info(f"Promemoria programmato per attività {task['id']} alle {reminder_time}")
        except Exception as e:
            logger.error(f"Errore programmazione promemoria: {e}")
    
    def check_reminders(self, now):
        """Controlla se ci sono promemoria da inviare"""
        to_remove = []
        
        for task_id, reminder_time in self.reminders.items():
            if now >= reminder_time:
                self.send_reminder(task_id)
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.reminders[task_id]
    
    def send_reminder(self, task_id):
        """Invia un promemoria 5 minuti prima di un'attività"""
        if not CHAT_ID:
            logger.error("CHAT_ID non configurato")
            return
        
        try:
            task = self.db.get_task_by_id(task_id)
            if task and not task['completed']:
                message = f"⏰ Promemoria!\n\nFra 5 minuti devi:\n{task['description']}\n\nOra: {task['time']}"
                threading.Thread(target=self._send_message_sync, args=(message,)).start()
                logger.info(f"Promemoria inviato per attività {task_id}")
        except Exception as e:
            logger.error(f"Errore invio promemoria: {e}")
    
    def refresh_reminders(self):
        """Ricarica tutti i promemoria (chiamato dopo aggiunta/modifica attività)"""
        self.load_reminders()
    
    def shutdown(self):
        """Ferma lo scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler fermato")
