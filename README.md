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

## 🌐 Deploy gratis consigliato

Il modo più semplice per tenerlo online gratis è:

1. **Supabase free** per salvare gli impegni
2. **Render free** come Web Service
3. **UptimeRobot free** per pingare l'endpoint `/health`

### Perché così

- Il database non si perde se Render si riavvia
- Il bot resta raggiungibile tramite HTTP
- Il ping ogni 5 minuti evita lo sleep del servizio

### Passi rapidi

#### 1. Crea il database su Supabase

1. Vai su [supabase.com](https://supabase.com)
2. Crea un progetto nuovo
3. Apri **Project Settings** -> **Database**
4. Copia la stringa di connessione PostgreSQL
5. Tienila da parte come `DATABASE_URL`

#### 2. Prepara il file `.env`

Crea un file `.env` partendo da `.env.example` e inserisci:

```env
TELEGRAM_BOT_TOKEN=il_tuo_token
TELEGRAM_CHAT_ID=il_tuo_chat_id
DATABASE_URL=postgresql://...
```

Se stai lavorando in locale puoi anche lasciare `DATABASE_URL` vuoto e il bot userà `tasks.db`.

#### 3. Carica tutto su GitHub

```bash
git init
git add .
git commit -m "Prepare bot for Render and Supabase"
git branch -M main
git remote add origin https://github.com/TUO_USERNAME/TUO_REPO.git
git push -u origin main
```

#### 4. Crea il Web Service su Render

1. Vai su [render.com](https://render.com)
2. Collega GitHub
3. Crea un **Web Service**
4. Scegli il tuo repository
5. Lascia che Render usi:
   - `buildCommand: pip install -r requirements.txt`
   - `startCommand: python bot.py`
6. Imposta le variabili d'ambiente:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `DATABASE_URL`

#### 5. Crea il ping gratuito

1. Vai su [uptimerobot.com](https://uptimerobot.com)
2. Crea un monitor **HTTP**
3. Inserisci l'URL del tuo servizio Render con `/health`
4. Imposta il controllo ogni 5 minuti

#### 6. Verifica

- In Render guarda i log
- Apri `https://tuo-servizio.onrender.com/health`
- In Telegram prova `/start`
- Aggiungi un task con `/aggiungi descrizione | 2026-06-26 | 14:30`

### Importante

- Render Free può comunque riavviare il servizio in alcuni casi
- Supabase tiene gli impegni al sicuro anche se il bot riparte
- Il file `tasks.db` serve solo come fallback locale

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
