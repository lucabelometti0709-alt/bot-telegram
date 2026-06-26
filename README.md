# 🤖 Bot Telegram Daily Tasks

Un bot Telegram completo per gestire le tue attività giornaliere con promemoria automatici e interfaccia grafica.

## ✨ Funzionalità

- 📋 **Interfaccia grafica** per inserire e gestire le attività
- 📢 **Messaggio automatico alle 8:00** con la lista delle attività del giorno
- ⏰ **Promemoria 5 minuti prima** di ogni attività
- 💬 **Comandi Telegram** per consultare la todolist
- ✅ **Segna attività come completate**
- 🗑️ **Elimina attività**
- 📅 **Visualizza attività di oggi o tutte le attività**

## 📦 Installazione

1. Clona o scarica questo repository

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura le variabili d'ambiente:
   - Copia il file `.env.example` in `.env`
   - Inserisci il tuo token del bot Telegram (ottenuto da @BotFather)
   - Inserisci il tuo Chat ID (per ricevere i messaggi automatici)

```bash
cp .env.example .env
```

Modifica il file `.env`:
```
TELEGRAM_BOT_TOKEN=il_tuo_token_qui
TELEGRAM_CHAT_ID=il_tuo_chat_id_qui
```

### Come ottenere il Chat ID

1. Avvia il bot (vedi sotto)
2. Invia un messaggio al bot su Telegram
3. Visita questo URL nel browser:
   ```
   https://api.telegram.org/bot<TUO_TOKEN>/getUpdates
   ```
4. Cerca il campo `"chat":{"id":NUMERO}` - quel numero è il tuo Chat ID

## 🚀 Utilizzo

### Avviare il Bot Telegram

```bash
python bot.py
```

Il bot rimarrà in esecuzione e:
- Risponderà ai comandi Telegram
- Invierà automaticamente il messaggio delle 8:00
- Invierà i promemoria 5 minuti prima di ogni attività

### Avviare l'Interfaccia Grafica

```bash
python gui.py
```

L'interfaccia grafica ti permette di:
- Aggiungere nuove attività
- Visualizzare le attività di oggi o tutte
- Segnare attività come completate
- Eliminare attività

## 📱 Comandi Telegram

- `/start` - Avvia il bot e mostra i comandi disponibili
- `/aiuto` o `/help` - Mostra i comandi disponibili
- `/oggi` - Mostra le attività di oggi
- `/tutte` - Mostra tutte le attività
- `/aggiungi descrizione | data (YYYY-MM-DD) | ora (HH:MM)` - Aggiunge una nuova attività
- `/completa [ID]` - Segna un'attività come completata
- `/elimina [ID]` - Elimina un'attività

### Esempio di aggiunta attività

```
/aggiungi Riunione di lavoro | 2024-06-26 | 14:30
```

## 📁 Struttura del Progetto

```
bot/
├── bot.py              # Bot Telegram principale
├── database.py         # Gestione database SQLite
├── scheduler.py        # Sistema di scheduling per promemoria
├── gui.py              # Interfaccia grafica
├── requirements.txt    # Dipendenze Python
├── .env.example        # Esempio configurazione
├── .env                # Configurazione personale (da creare)
├── tasks.db            # Database SQLite (creato automaticamente)
└── README.md           # Questo file
```

## 🔧 Configurazione Avanzata

### Modificare l'orario del messaggio giornaliero

Modifica il file `scheduler.py`, cerca la funzione `start()` e cambia:
```python
CronTrigger(hour=8, minute=0)
```
con l'orario desiderato.

### Modificare il tempo del promemoria

Modifica il file `scheduler.py`, cerca la funzione `schedule_reminder()` e cambia:
```python
reminder_time = task_datetime - timedelta(minutes=5)
```
con il numero di minuti desiderato.

## 🌐 Deploy su Render

Per tenere il bot online 24/7, puoi usare Render (piano gratuito disponibile). Ecco i passaggi:

### 1. Prepara il repository

Assicurati di avere i file seguenti nel tuo repository:
- `Procfile` (già creato)
- `render.yaml` (già creato)
- `.gitignore` (già creato)
- `requirements.txt`
- Tutti i file Python (`bot.py`, `database.py`, `scheduler.py`)

### 2. Crea un repository su GitHub

1. Vai su [GitHub](https://github.com) e crea un nuovo repository
2. Carica i file del progetto:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TUO_USERNAME/TUO_REPO.git
git push -u origin main
```

### 3. Crea un account su Render

1. Vai su [render.com](https://render.com)
2. Registrati con il tuo account GitHub
3. Autorizza Render ad accedere ai tuoi repository

### 4. Crea il Web Service su Render

1. Clicca su **"New +"** → **"Web Service"**
2. Seleziona il tuo repository GitHub
3. Render rileverà automaticamente il file `render.yaml`
4. Configura le variabili d'ambiente:
   - `TELEGRAM_BOT_TOKEN`: Il tuo token da @BotFather
   - `TELEGRAM_CHAT_ID`: Il tuo Chat ID
5. Clicca su **"Create Web Service"**

### 5. Verifica il deploy

1. Render inizierà automaticamente il deploy
2. Puoi monitorare i log nella sezione **"Logs"**
3. Una volta completato, il bot sarà online 24/7

### 6. Cron Job per mantenere attivo il bot

Render ha un piano gratuito che mette in sleep i servizi dopo 15 minuti di inattività. Per evitare questo:

**Opzione A: Usa un servizio di ping esterno**
- Usa [uptimerobot.com](https://uptimerobot.com) (gratuito)
- Crea un monitor che pinga il tuo endpoint ogni 5 minuti
- Nota: Render Worker non ha endpoint HTTP, quindi questa opzione potrebbe non funzionare

**Opzione B: Usa Render Cron Jobs**
1. Crea un nuovo **Cron Job** su Render
2. Collegalo allo stesso repository
3. Imposta il comando: `python -c "import requests; requests.get('https://TUO_BOT_URL')"`
4. Imposta la frequenza: ogni 5-10 minuti

**Opzione C: Upgrade al piano Starter ($7/mese)**
- Il piano Starter evita il sleep mode
- Ideale per bot che devono essere sempre attivi

### 7. Monitoraggio

- Controlla i log regolarmente su Render
- Il bot si riavvierà automaticamente in caso di crash
- Puoi vedere le metriche di utilizzo nella dashboard

## 🛠️ Troubleshooting

### Il bot non invia messaggi automatici

- Assicurati di aver configurato correttamente il `CHAT_ID` nel file `.env`
- Verifica che il bot sia in esecuzione
- Controlla i log per eventuali errori

### Il database non viene creato

- Il database `tasks.db` viene creato automaticamente alla prima esecuzione
- Assicurati di avere i permessi di scrittura nella cartella

### Errori di dipendenze

- Reinstalla le dipendenze: `pip install -r requirements.txt --upgrade`
- Assicurati di usare Python 3.7 o superiore

## 📝 Note

- Il bot deve rimanere in esecuzione per inviare i messaggi automatici
- Per eseguire il bot 24/7, considera di usare un server VPS o servizi come Heroku/Render
- Il database SQLite è locale e non richiede configurazione aggiuntiva

## 🤝 Contributi

Sentiti libero di aprire issue o pull request per miglioramenti!

## 📄 Licenza

Questo progetto è open source e disponibile per uso personale.
