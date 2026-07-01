import os
import logging
import threading
import time
from datetime import datetime, timedelta
from pytz import timezone, UTC
from telegram import Bot
from dotenv import load_dotenv
from database import Database

# Carica le variabili d'ambiente
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TIMEZONE_STR = os.getenv('TIMEZONE', 'Europe/Rome')
DAILY_MESSAGE_HOUR = int(os.getenv('DAILY_MESSAGE_HOUR', '8'))
DAILY_MESSAGE_MINUTE = int(os.getenv('DAILY_MESSAGE_MINUTE', '0'))
REMINDER_MINUTES_BEFORE = int(os.getenv('REMINDER_MINUTES_BEFORE', '5'))
AUTO_DELETE_MINUTES_AFTER = int(os.getenv('AUTO_DELETE_MINUTES_AFTER', '1'))

# Configura il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    USER_TIMEZONE = timezone(TIMEZONE_STR)
    logger.info(f"Fuso orario configurato: {TIMEZONE_STR}")
except Exception as e:
    logger.warning(f"Fuso orario non valido: {TIMEZONE_STR}, uso il sistema. Errore: {e}")
    USER_TIMEZONE = timezone('UTC')


def get_now():
    """Ritorna l'ora corrente nel fuso orario dell'utente"""
    return datetime.now(USER_TIMEZONE)


def get_today():
    """Ritorna la data odierna nel fuso orario dell'utente (formato YYYY-MM-DD)"""
    return get_now().strftime('%Y-%m-%d')


class TaskScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()
        self.running = False
        self.thread = None
        self.reminders = {}  # {task_id: reminder_time}
        self.expired_tasks = set()  # Traccia task scaduti per evitare doppi check
    
    def start(self):
        """Avvia lo scheduler in un thread separato"""
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info(f"Scheduler avviato con fuso orario: {TIMEZONE_STR}")
        logger.info(f"Auto-delete abilitato: elimina task dopo {AUTO_DELETE_MINUTES_AFTER} minuto/i")
        
        # Carica i promemoria esistenti
        self.load_reminders()
    
    def _run_scheduler(self):
        """Loop principale dello scheduler"""
        last_daily_check = None
        
        while self.running:
            try:
                now = get_now()
                
                # Controlla se è ora del messaggio giornaliero
                if now.hour == DAILY_MESSAGE_HOUR and now.minute == DAILY_MESSAGE_MINUTE:
                    if last_daily_check != now.date():
                        self.send_daily_message()
                        last_daily_check = now.date()
                
                # Controlla i promemoria
                self.check_reminders(now)
                
                # Controlla e elimina task scaduti
                self.check_expired_tasks(now)
                
                # Dormi 10 secondi
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Errore nello scheduler: {e}")
                time.sleep(10)
    
    def send_daily_message(self):
        """Invia il messaggio giornaliero all'ora configurata"""
        if not CHAT_ID:
            logger.error("CHAT_ID non configurato")
            return
        
        try:
            today = get_today()
            tasks = self.db.get_tasks_by_date(today)
            
            now = get_now()
            message = f"🌅 Buongiorno! Ecco cosa devi fare oggi ({today}) - Fuso orario: {TIMEZONE_STR}\n\n"
            
            if not tasks:
                message += "Nessuna attività programmata per oggi. 🎉"
            else:
                for task in tasks:
                    status = "✅" if task['completed'] else "⏳"
                    message += f"{status} {task['time']} - {task['description']}\n"
            
            # Usa un thread per inviare il messaggio (operazione async in thread sync)
            threading.Thread(target=self._send_message_sync, args=(message,)).start()
            logger.info(f"Messaggio giornaliero inviato alle {DAILY_MESSAGE_HOUR}:{DAILY_MESSAGE_MINUTE:02d}")
            
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
        """Programma un promemoria N minuti prima di un'attività"""
        try:
            task_datetime = datetime.strptime(f"{task['date']} {task['time']}", '%Y-%m-%d %H:%M')
            # Rendi la data locale nel fuso orario dell'utente
            task_datetime = USER_TIMEZONE.localize(task_datetime)
            
            reminder_time = task_datetime - timedelta(minutes=REMINDER_MINUTES_BEFORE)
            
            # Se il promemoria è nel futuro, salvalo
            if reminder_time > get_now():
                self.reminders[task['id']] = reminder_time
                logger.info(f"Promemoria programmato per attività {task['id']} alle {reminder_time.strftime('%Y-%m-%d %H:%M')} ({TIMEZONE_STR})")
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
        """Invia un promemoria N minuti prima di un'attività"""
        if not CHAT_ID:
            logger.error("CHAT_ID non configurato")
            return
        
        try:
            task = self.db.get_task_by_id(task_id)
            if task and not task['completed']:
                message = f"⏰ Promemoria!\n\nFra {REMINDER_MINUTES_BEFORE} minuti devi:\n{task['description']}\n\nOra: {task['time']} ({TIMEZONE_STR})"
                threading.Thread(target=self._send_message_sync, args=(message,)).start()
                logger.info(f"Promemoria inviato per attività {task_id}")
        except Exception as e:
            logger.error(f"Errore invio promemoria: {e}")
    
    def check_expired_tasks(self, now):
        """Controlla e elimina automaticamente i task scaduti"""
        try:
            tasks = self.db.get_all_tasks()
            
            for task in tasks:
                # Se il task è già completato, saltalo
                if task['completed']:
                    continue
                
                # Se abbiamo già processato questo task, saltalo
                if task['id'] in self.expired_tasks:
                    continue
                
                try:
                    # Parsa la data e ora del task
                    task_datetime = datetime.strptime(
                        f"{task['date']} {task['time']}", 
                        '%Y-%m-%d %H:%M'
                    )
                    # Rendi la data locale nel fuso orario dell'utente
                    task_datetime = USER_TIMEZONE.localize(task_datetime)
                    
                    # Calcola il tempo di scadenza (orario + minuti configurati)
                    expiration_time = task_datetime + timedelta(minutes=AUTO_DELETE_MINUTES_AFTER)
                    
                    # Se è passato il tempo di scadenza, elimina il task
                    if now > expiration_time:
                        self.db.delete_task(task['id'])
                        self.expired_tasks.add(task['id'])
                        logger.info(
                            f"🗑️ Task {task['id']} (\"{task['description']}\") "
                            f"scaduto e eliminato automaticamente. "
                            f"Orario: {task['date']} {task['time']}, "
                            f"eliminato alle: {now.strftime('%Y-%m-%d %H:%M:%S')} ({TIMEZONE_STR})"
                        )
                except Exception as e:
                    logger.error(f"Errore nel processamento task {task['id']}: {e}")
        
        except Exception as e:
            logger.error(f"Errore nel check dei task scaduti: {e}")
    
    def refresh_reminders(self):
        """Ricarica tutti i promemoria (chiamato dopo aggiunta/modifica attività)"""
        self.load_reminders()
        # Ripulisci la lista dei task scaduti per permettere il reprocessamento
        self.expired_tasks.clear()
    
    def shutdown(self):
        """Ferma lo scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler fermato")
