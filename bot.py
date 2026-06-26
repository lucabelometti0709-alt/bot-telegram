import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
from database import Database
from scheduler import TaskScheduler

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

# Inizializza il database
db = Database()
# Lo scheduler sarà inizializzato nel main
scheduler = None

def format_tasks_message(tasks, title="Le tue attività:"):
    """Formatta la lista delle attività in un messaggio"""
    if not tasks:
        return f"{title}\n\nNessuna attività programmata."
    
    message = f"{title}\n\n"
    for task in tasks:
        status = "✅" if task['completed'] else "⏳"
        message += f"{status} {task['time']} - {task['description']}\n"
    
    return message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_message = """
🤖 Benvenuto al tuo Bot Daily Tasks!

Ecco i comandi disponibili:
📋 /oggi - Mostra le attività di oggi
📅 /tutte - Mostra tutte le attività
➕ /aggiungi - Aggiungi una nuova attività
✅ /completa [ID] - Segna attività come completata
🗑️ /elimina [ID] - Elimina un'attività
ℹ️ /aiuto - Mostra questo messaggio

Il bot ti invierà automaticamente:
- 📢 Alle 8:00 la lista delle attività del giorno
- ⏰ 5 minuti prima di ogni attività un promemoria
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /aiuto"""
    help_message = """
📚 Comandi disponibili:

📋 /oggi - Mostra le attività di oggi
📅 /tutte - Mostra tutte le attività
➕ /aggiungi - Aggiungi una nuova attività
✅ /completa [ID] - Segna attività come completata
🗑️ /elimina [ID] - Elimina un'attività
ℹ️ /aiuto - Mostra questo messaggio

💡 Per aggiungere un'attività, usa il comando /aggiungi seguito da:
descrizione | data (YYYY-MM-DD) | ora (HH:MM)

Esempio: /aggiungi Riunione di lavoro | 2024-06-26 | 14:30
    """
    await update.message.reply_text(help_message)

async def today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /oggi - Mostra le attività di oggi"""
    today = datetime.now().strftime('%Y-%m-%d')
    tasks = db.get_tasks_by_date(today)
    message = format_tasks_message(tasks, f"📋 Attività di oggi ({today}):")
    await update.message.reply_text(message)

async def all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /tutte - Mostra tutte le attività"""
    tasks = db.get_all_tasks()
    message = format_tasks_message(tasks, "📅 Tutte le attività:")
    await update.message.reply_text(message)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /aggiungi - Aggiunge una nuova attività"""
    if not context.args:
        await update.message.reply_text(
            "❌ Uso corretto: /aggiungi descrizione | data (YYYY-MM-DD) | ora (HH:MM)\n"
            "Esempio: /aggiungi Riunione di lavoro | 2024-06-26 | 14:30"
        )
        return
    
    try:
        # Unisci gli argomenti
        full_text = ' '.join(context.args)
        
        # Separa i componenti
        parts = [part.strip() for part in full_text.split('|')]
        
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ Formato non valido. Usa: descrizione | data (YYYY-MM-DD) | ora (HH:MM)"
            )
            return
        
        description = parts[0]
        date = parts[1]
        time = parts[2]
        
        # Valida il formato data
        datetime.strptime(date, '%Y-%m-%d')
        
        # Valida il formato ora
        datetime.strptime(time, '%H:%M')
        
        task_id = db.add_task(description, date, time)
        
        # Aggiorna lo scheduler
        if scheduler:
            scheduler.refresh_reminders()
        
        await update.message.reply_text(
            f"✅ Attività aggiunta!\n\n"
            f"ID: {task_id}\n"
            f"Descrizione: {description}\n"
            f"Data: {date}\n"
            f"Ora: {time}"
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Errore nel formato: {str(e)}\n"
            "Usa il formato: data (YYYY-MM-DD) e ora (HH:MM)"
        )

async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /completa - Segna un'attività come completata"""
    if not context.args:
        await update.message.reply_text("❌ Uso corretto: /completa [ID]")
        return
    
    try:
        task_id = int(context.args[0])
        if db.mark_completed(task_id):
            # Aggiorna lo scheduler
            if scheduler:
                scheduler.refresh_reminders()
            await update.message.reply_text(f"✅ Attività {task_id} segnata come completata!")
        else:
            await update.message.reply_text(f"❌ Attività {task_id} non trovata.")
    except ValueError:
        await update.message.reply_text("❌ L'ID deve essere un numero.")

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /elimina - Elimina un'attività"""
    if not context.args:
        await update.message.reply_text("❌ Uso corretto: /elimina [ID]")
        return
    
    try:
        task_id = int(context.args[0])
        if db.delete_task(task_id):
            # Aggiorna lo scheduler
            if scheduler:
                scheduler.refresh_reminders()
            await update.message.reply_text(f"🗑️ Attività {task_id} eliminata!")
        else:
            await update.message.reply_text(f"❌ Attività {task_id} non trovata.")
    except ValueError:
        await update.message.reply_text("❌ L'ID deve essere un numero.")

def main():
    """Avvia il bot"""
    global scheduler
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN non configurato")
        return
    
    # Crea l'applicazione
    application = Application.builder().token(TOKEN).build()
    
    # Inizializza lo scheduler
    scheduler = TaskScheduler(application.bot)
    scheduler.start()
    
    # Aggiungi i handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("aiuto", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("oggi", today_tasks))
    application.add_handler(CommandHandler("tutte", all_tasks))
    application.add_handler(CommandHandler("aggiungi", add_task))
    application.add_handler(CommandHandler("completa", complete_task))
    application.add_handler(CommandHandler("elimina", delete_task))
    
    # Avvia il bot
    logger.info("Bot avviato!")
    try:
        application.run_polling()
    finally:
        scheduler.shutdown()

if __name__ == '__main__':
    main()
