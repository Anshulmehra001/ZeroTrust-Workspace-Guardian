import tkinter as tk
from tkinter import ttk, scrolledtext
import sqlite3
from datetime import datetime
import os

class SecurityDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("ZeroTrust Workspace Guardian - Security Dashboard")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')
        
        # Header
        header = tk.Frame(root, bg='#d32f2f', height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="🛡️ ZeroTrust Workspace Guardian",
                        font=('Arial', 24, 'bold'), bg='#d32f2f', fg='white')
        title.pack(pady=20)
        
        # Stats Frame
        stats_frame = tk.Frame(root, bg='#2e2e2e', pady=20)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.create_stat_card(stats_frame, "Total Threats", "0", 0)
        self.create_stat_card(stats_frame, "Shoulder Surfing", "0", 1)
        self.create_stat_card(stats_frame, "Camera Detected", "0", 2)
        self.create_stat_card(stats_frame, "User Absence", "0", 3)
        
        # Threat Log
        log_label = tk.Label(root, text="Recent Security Events",
                            font=('Arial', 16, 'bold'), bg='#1e1e1e', fg='white')
        log_label.pack(pady=(20, 10))
        
        # Create Treeview for logs
        columns = ('ID', 'Time', 'Threat Type', 'Faces', 'Action', 'Screenshot')
        self.tree = ttk.Treeview(root, columns=columns, show='headings', height=15)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Time', text='Timestamp')
        self.tree.heading('Threat Type', text='Threat Type')
        self.tree.heading('Faces', text='Faces')
        self.tree.heading('Action', text='Action Taken')
        self.tree.heading('Screenshot', text='Evidence')
        
        # Define column widths
        self.tree.column('ID', width=50)
        self.tree.column('Time', width=150)
        self.tree.column('Threat Type', width=180)
        self.tree.column('Faces', width=80)
        self.tree.column('Action', width=150)
        self.tree.column('Screenshot', width=250)
        
        self.tree.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = tk.Frame(root, bg='#1e1e1e')
        button_frame.pack(pady=10)
        
        refresh_btn = tk.Button(button_frame, text="🔄 Refresh", command=self.load_data,
                               bg='#4caf50', fg='white', font=('Arial', 12, 'bold'),
                               padx=20, pady=10, cursor='hand2')
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(button_frame, text="📊 Export Report", command=self.export_report,
                              bg='#2196f3', fg='white', font=('Arial', 12, 'bold'),
                              padx=20, pady=10, cursor='hand2')
        export_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear Logs", command=self.clear_logs,
                             bg='#f44336', fg='white', font=('Arial', 12, 'bold'),
                             padx=20, pady=10, cursor='hand2')
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Load initial data
        self.load_data()
        
        # Auto-refresh every 5 seconds
        self.auto_refresh()
    
    def create_stat_card(self, parent, title, value, column):
        card = tk.Frame(parent, bg='#3e3e3e', relief=tk.RAISED, borderwidth=2)
        card.grid(row=0, column=column, padx=10, pady=5, sticky='ew')
        parent.columnconfigure(column, weight=1)
        
        title_label = tk.Label(card, text=title, font=('Arial', 12),
                              bg='#3e3e3e', fg='#aaaaaa')
        title_label.pack(pady=(10, 5))
        
        value_label = tk.Label(card, text=value, font=('Arial', 24, 'bold'),
                              bg='#3e3e3e', fg='#ffffff')
        value_label.pack(pady=(5, 10))
        
        # Store reference for updating
        setattr(self, f'stat_{column}', value_label)
    
    def load_data(self):
        """Load threat data from database"""
        if not os.path.exists('security_log.db'):
            return
        
        conn = sqlite3.connect('security_log.db')
        cursor = conn.cursor()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load all threats
        cursor.execute('SELECT * FROM threats ORDER BY id DESC')
        threats = cursor.fetchall()
        
        for threat in threats:
            threat_id, timestamp, threat_type, face_count, action, screenshot, location = threat
            screenshot_display = os.path.basename(screenshot) if screenshot else "N/A"
            self.tree.insert('', tk.END, values=(
                threat_id, timestamp, threat_type, face_count, action, screenshot_display
            ))
        
        # Update stats
        total = len(threats)
        shoulder = len([t for t in threats if 'Shoulder' in t[2]])
        camera = len([t for t in threats if 'Camera' in t[2]])
        absence = len([t for t in threats if 'Absence' in t[2]])
        
        self.stat_0.config(text=str(total))
        self.stat_1.config(text=str(shoulder))
        self.stat_2.config(text=str(camera))
        self.stat_3.config(text=str(absence))
        
        conn.close()
    
    def export_report(self):
        """Export security report"""
        if not os.path.exists('security_log.db'):
            return
        
        conn = sqlite3.connect('security_log.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM threats ORDER BY timestamp DESC')
        threats = cursor.fetchall()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'security_report_{timestamp}.txt'
        
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ZEROTRUST WORKSPACE GUARDIAN - SECURITY REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Threats Detected: {len(threats)}\n\n")
            f.write("-" * 80 + "\n\n")
            
            for threat in threats:
                f.write(f"Threat ID: {threat[0]}\n")
                f.write(f"Timestamp: {threat[1]}\n")
                f.write(f"Type: {threat[2]}\n")
                f.write(f"Face Count: {threat[3]}\n")
                f.write(f"Action Taken: {threat[4]}\n")
                f.write(f"Evidence: {threat[5] or 'N/A'}\n")
                f.write("-" * 80 + "\n\n")
        
        conn.close()
        print(f"✅ Report exported: {filename}")
    
    def clear_logs(self):
        """Clear all threat logs"""
        if not os.path.exists('security_log.db'):
            return
        
        conn = sqlite3.connect('security_log.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM threats')
        conn.commit()
        conn.close()
        
        self.load_data()
        print("✅ Logs cleared")
    
    def auto_refresh(self):
        """Auto-refresh data every 5 seconds"""
        self.load_data()
        self.root.after(5000, self.auto_refresh)

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityDashboard(root)
    root.mainloop()
