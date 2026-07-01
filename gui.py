import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pytz import timezone
import os
from dotenv import load_dotenv
from database import Database

load_dotenv()

# Carica il fuso orario configurato
TIMEZONE_STR = os.getenv('TIMEZONE', 'Europe/Rome')
try:
    USER_TIMEZONE = timezone(TIMEZONE_STR)
except Exception as e:
    print(f"Fuso orario non valido: {TIMEZONE_STR}, uso il sistema. Errore: {e}")
    USER_TIMEZONE = timezone('UTC')


def get_now():
    """Ritorna l'ora corrente nel fuso orario dell'utente"""
    return datetime.now(USER_TIMEZONE)


def get_today():
    """Ritorna la data odierna nel fuso orario dell'utente (formato YYYY-MM-DD)"""
    return get_now().strftime('%Y-%m-%d')


class TaskManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Gestione Attività Bot Telegram - Fuso: {TIMEZONE_STR}")
        self.root.geometry("800x600")
        
        self.db = Database()
        
        # Crea i widget
        self.create_widgets()
        
        # Carica le attività
        self.refresh_tasks()
    
    def create_widgets(self):
        """Crea tutti i widget dell'interfaccia"""
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text=f"📋 Gestione Attività - Fuso: {TIMEZONE_STR}", 
            font=('Arial', 14, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Ora corrente
        current_time_label = ttk.Label(
            main_frame,
            text=f"Ora corrente: {get_now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=('Arial', 9)
        )
        current_time_label.grid(row=0, column=2, sticky=tk.E, pady=(0, 20))
        self.current_time_label = current_time_label
        
        # Frame per l'inserimento
        input_frame = ttk.LabelFrame(main_frame, text="Aggiungi Nuova Attività", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Descrizione
        ttk.Label(input_frame, text="Descrizione:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.description_entry = ttk.Entry(input_frame, width=50)
        self.description_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Data
        ttk.Label(input_frame, text="Data (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=20)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        # Imposta la data di oggi come default (nel fuso orario dell'utente)
        self.date_entry.insert(0, get_today())
        
        # Ora
        ttk.Label(input_frame, text="Ora (HH:MM):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.time_entry = ttk.Entry(input_frame, width=20)
        self.time_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Pulsante Aggiungi
        add_button = ttk.Button(input_frame, text="➕ Aggiungi", command=self.add_task)
        add_button.grid(row=3, column=1, sticky=tk.W, pady=10)
        
        # Frame per i filtri
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(filter_frame, text="📋 Oggi", command=self.show_today).grid(row=0, column=0, padx=5)
        ttk.Button(filter_frame, text="📅 Tutte", command=self.show_all).grid(row=0, column=1, padx=5)
        ttk.Button(filter_frame, text="🔄 Aggiorna ora", command=self.update_current_time).grid(row=0, column=2, padx=5)
        
        # Tabella delle attività
        table_frame = ttk.LabelFrame(main_frame, text="Attività", padding="10")
        table_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Treeview
        columns = ('ID', 'Descrizione', 'Data', 'Ora', 'Stato')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Configura le colonne
        self.tree.heading('ID', text='ID')
        self.tree.column('ID', width=50, anchor=tk.CENTER)
        
        self.tree.heading('Descrizione', text='Descrizione')
        self.tree.column('Descrizione', width=300, anchor=tk.W)
        
        self.tree.heading('Data', text='Data')
        self.tree.column('Data', width=100, anchor=tk.CENTER)
        
        self.tree.heading('Ora', text='Ora')
        self.tree.column('Ora', width=80, anchor=tk.CENTER)
        
        self.tree.heading('Stato', text='Stato')
        self.tree.column('Stato', width=80, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Frame per le azioni
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(action_frame, text="✅ Completa", command=self.complete_task).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="🗑️ Elimina", command=self.delete_task).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="🔄 Aggiorna pagina", command=self.refresh_tasks).grid(row=0, column=2, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Pronto - Fuso orario: {TIMEZONE_STR}")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.current_filter = 'all'
    
    def update_current_time(self):
        """Aggiorna l'ora corrente visualizzata"""
        current_time_str = f"Ora corrente: {get_now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.current_time_label.config(text=current_time_str)
    
    def add_task(self):
        """Aggiunge una nuova attività"""
        description = self.description_entry.get().strip()
        date = self.date_entry.get().strip()
        time = self.time_entry.get().strip()
        
        if not description or not date or not time:
            messagebox.showerror("Errore", "Compila tutti i campi!")
            return
        
        try:
            # Valida il formato data
            datetime.strptime(date, '%Y-%m-%d')
            
            # Valida il formato ora
            datetime.strptime(time, '%H:%M')
            
            task_id = self.db.add_task(description, date, time)
            self.status_var.set(f"✅ Attività aggiunta con ID {task_id}")
            
            # Pulisci i campi
            self.description_entry.delete(0, tk.END)
            self.time_entry.delete(0, tk.END)
            
            # Aggiorna la lista
            self.refresh_tasks()
            
        except ValueError as e:
            messagebox.showerror("Errore", f"Formato non valido: {str(e)}\nUsa YYYY-MM-DD per la data e HH:MM per l'ora")
    
    def refresh_tasks(self):
        """Aggiorna la lista delle attività"""
        # Pulisci la tabella
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Carica le attività in base al filtro
        if self.current_filter == 'today':
            today = get_today()
            tasks = self.db.get_tasks_by_date(today)
        else:
            tasks = self.db.get_all_tasks()
        
        # Popola la tabella
        for task in tasks:
            status = "✅ Completata" if task['completed'] else "⏳ In corso"
            self.tree.insert('', tk.END, values=(
                task['id'],
                task['description'],
                task['date'],
                task['time'],
                status
            ))
        
        self.status_var.set(f"Caricate {len(tasks)} attività - Ora corrente ({TIMEZONE_STR}): {get_now().strftime('%H:%M:%S')}")
        self.update_current_time()
    
    def show_today(self):
        """Mostra le attività di oggi"""
        self.current_filter = 'today'
        self.refresh_tasks()
    
    def show_all(self):
        """Mostra tutte le attività"""
        self.current_filter = 'all'
        self.refresh_tasks()
    
    def complete_task(self):
        """Segna l'attività selezionata come completata"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un'attività!")
            return
        
        item = self.tree.item(selected[0])
        task_id = item['values'][0]
        
        if self.db.mark_completed(task_id):
            self.status_var.set(f"✅ Attività {task_id} completata")
            self.refresh_tasks()
        else:
            messagebox.showerror("Errore", "Impossibile completare l'attività")
    
    def delete_task(self):
        """Elimina l'attività selezionata"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un'attività!")
            return
        
        item = self.tree.item(selected[0])
        task_id = item['values'][0]
        
        if messagebox.askyesno("Conferma", f"Sei sicuro di voler eliminare l'attività {task_id}?"):
            if self.db.delete_task(task_id):
                self.status_var.set(f"🗑️ Attività {task_id} eliminata")
                self.refresh_tasks()
            else:
                messagebox.showerror("Errore", "Impossibile eliminare l'attività")

def main():
    root = tk.Tk()
    app = TaskManagerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
