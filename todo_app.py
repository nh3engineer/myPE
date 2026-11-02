"""TODO Desktop-App mit Tkinter (erweiterte Version)."""

import json
import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, simpledialog, ttk

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

PRIORITIES = ["niedrig", "mittel", "hoch"]


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TODO App")
        self.root.geometry("560x560")
        self.root.minsize(480, 450)

        self.tasks = self.load_tasks()
        self.filter_var = tk.StringVar(value="alle")

        self.build_input_area()
        self.build_filter_area()
        self.build_list_area()
        self.build_button_area()
        self.refresh_list()

    def build_input_area(self):
        frame = ttk.LabelFrame(self.root, text="Neue Aufgabe", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.entry = ttk.Entry(frame)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", lambda e: self.add_task())

        self.priority_var = tk.StringVar(value="mittel")
        ttk.Combobox(
            frame,
            textvariable=self.priority_var,
            values=PRIORITIES,
            state="readonly",
            width=8,
        ).grid(row=0, column=1, padx=(8, 0))

        self.due_var = tk.StringVar()
        due_entry = ttk.Entry(frame, textvariable=self.due_var, width=12)
        due_entry.grid(row=0, column=2, padx=(8, 0))
        due_entry.insert(0, "JJJJ-MM-TT")
        due_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(due_entry, "JJJJ-MM-TT"))

        ttk.Button(frame, text="Hinzufügen", command=self.add_task).grid(
            row=0, column=3, padx=(8, 0)
        )
        frame.columnconfigure(0, weight=1)

    def build_filter_area(self):
        frame = ttk.Frame(self.root, padding=(10, 0))
        frame.pack(fill=tk.X)

        for label, value in [("Alle", "alle"), ("Offen", "offen"), ("Erledigt", "erledigt")]:
            ttk.Radiobutton(
                frame, text=label, variable=self.filter_var, value=value,
                command=self.refresh_list,
            ).pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(frame, text="")
        self.status_label.pack(side=tk.RIGHT)

    def build_list_area(self):
        frame = ttk.Frame(self.root, padding=(10, 5))
        frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            frame,
            columns=("status", "task", "priority", "due"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("status", text="Erledigt")
        self.tree.heading("task", text="Aufgabe")
        self.tree.heading("priority", text="Priorität")
        self.tree.heading("due", text="Fällig")
        self.tree.column("status", width=60, anchor=tk.CENTER)
        self.tree.column("task", width=230)
        self.tree.column("priority", width=80, anchor=tk.CENTER)
        self.tree.column("due", width=90, anchor=tk.CENTER)

        self.tree.tag_configure("hoch", foreground="#c0392b")
        self.tree.tag_configure("mittel", foreground="#b9770e")
        self.tree.tag_configure("niedrig", foreground="#1e8449")
        self.tree.tag_configure("done", foreground="#909090")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda e: self.edit_task())

    def build_button_area(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.X)

        ttk.Button(frame, text="Erledigt umschalten", command=self.toggle_task).pack(side=tk.LEFT)
        ttk.Button(frame, text="Bearbeiten", command=self.edit_task).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(frame, text="Löschen", command=self.delete_task).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(frame, text="PDF exportieren", command=self.export_pdf).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(frame, text="Erledigte löschen", command=self.clear_done).pack(side=tk.RIGHT)

    @staticmethod
    def clear_placeholder(entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [self.normalize_task(t) for t in data]
            except (json.JSONDecodeError, OSError):
                return []
        return []

    @staticmethod
    def normalize_task(t):
        return {
            "text": str(t.get("text", "")),
            "done": bool(t.get("done", False)),
            "priority": t.get("priority", "mittel") if t.get("priority") in PRIORITIES else "mittel",
            "due": str(t.get("due", "") or ""),
        }

    def save_tasks(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def visible_tasks(self):
        f = self.filter_var.get()
        if f == "offen":
            return [(i, t) for i, t in enumerate(self.tasks) if not t["done"]]
        if f == "erledigt":
            return [(i, t) for i, t in enumerate(self.tasks) if t["done"]]
        return list(enumerate(self.tasks))

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for i, task in self.visible_tasks():
            tags = (task["priority"],) + (("done",) if task["done"] else ())
            self.tree.insert(
                "", tk.END, iid=str(i),
                values=("☑" if task["done"] else "☐", task["text"], task["priority"], task["due"]),
                tags=tags,
            )
        done = sum(1 for t in self.tasks if t["done"])
        self.status_label.config(text=f"{done} von {len(self.tasks)} erledigt")

    def add_task(self):
        text = self.entry.get().strip()
        if not text:
            messagebox.showwarning("Hinweis", "Bitte eine Aufgabe eingeben.")
            return
        due = self.due_var.get().strip()
        if due == "JJJJ-MM-TT":
            due = ""
        if due:
            try:
                date.fromisoformat(due)
            except ValueError:
                messagebox.showwarning("Hinweis", "Datum bitte als JJJJ-MM-TT eingeben (z. B. 2025-12-24).")
                return
        self.tasks.append({
            "text": text,
            "done": False,
            "priority": self.priority_var.get(),
            "due": due,
        })
        self.entry.delete(0, tk.END)
        self.due_var.set("JJJJ-MM-TT")
        self.save_tasks()
        self.refresh_list()

    def get_selected_index(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Hinweis", "Bitte eine Aufgabe auswählen.")
            return None
        return int(selection[0])

    def toggle_task(self):
        i = self.get_selected_index()
        if i is not None:
            self.tasks[i]["done"] = not self.tasks[i]["done"]
            self.save_tasks()
            self.refresh_list()

    def delete_task(self):
        i = self.get_selected_index()
        if i is not None:
            del self.tasks[i]
            self.save_tasks()
            self.refresh_list()

    def clear_done(self):
        if not any(t["done"] for t in self.tasks):
            return
        self.tasks = [t for t in self.tasks if not t["done"]]
        self.save_tasks()
        self.refresh_list()

    def edit_task(self):
        i = self.get_selected_index()
        if i is None:
            return
        task = self.tasks[i]

        new_text = simpledialog.askstring("Bearbeiten", "Aufgabe:", initialvalue=task["text"], parent=self.root)
        if new_text is None:
            return
        new_text = new_text.strip()
        if not new_text:
            messagebox.showwarning("Hinweis", "Die Aufgabe darf nicht leer sein.")
            return

        new_priority = simpledialog.askstring(
            "Bearbeiten", "Priorität (niedrig/mittel/hoch):",
            initialvalue=task["priority"], parent=self.root,
        )
        if new_priority is None:
            return
        new_priority = new_priority.strip().lower()
        if new_priority not in PRIORITIES:
            messagebox.showwarning("Hinweis", "Priorität muss 'niedrig', 'mittel' oder 'hoch' sein.")
            return

        new_due = simpledialog.askstring(
            "Bearbeiten", "Fällig (JJJJ-MM-TT, leer = kein Datum):",
            initialvalue=task["due"], parent=self.root,
        )
        if new_due is None:
            return
        new_due = new_due.strip()
        if new_due:
            try:
                date.fromisoformat(new_due)
            except ValueError:
                messagebox.showwarning("Hinweis", "Datum bitte als JJJJ-MM-TT eingeben.")
                return

        task.update({"text": new_text, "priority": new_priority, "due": new_due})
        self.save_tasks()
        self.refresh_list()


    def export_pdf(self):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            messagebox.showwarning(
                "PDF-Export",
                "Das Paket 'reportlab' wird benötigt.\n"
                "Bitte einmalig installieren mit:\n\n"
                "pip install reportlab",
            )
            return

        if not self.tasks:
            messagebox.showwarning("Hinweis", "Keine Aufgaben zum Exportieren.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF-Dateien", "*.pdf")],
            initialfile=f"todo_export_{date.today().isoformat()}.pdf",
            title="Als PDF exportieren",
        )
        if not path:
            return

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        )
        elements = [
            Paragraph(f"TODO-Liste – Stand {date.today().strftime('%d.%m.%Y')}", styles["Title"]),
            Spacer(1, 0.4 * cm),
        ]

        priority_rank = {"hoch": 0, "mittel": 1, "niedrig": 2}
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (t["done"], priority_rank.get(t["priority"], 1), t["due"] or "9999-99-99"),
        )

        data = [["Status", "Aufgabe", "Priorität", "Fällig"]]
        for t in sorted_tasks:
            data.append([
                "[x]" if t["done"] else "[ ]",
                Paragraph(t["text"], styles["Normal"]),
                t["priority"],
                t["due"] or "-",
            ])

        table = Table(data, colWidths=[1.6 * cm, 10 * cm, 2.6 * cm, 2.8 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EDF2FA")]),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ]))
        elements.append(table)

        done = sum(1 for t in self.tasks if t["done"])
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(f"{done} von {len(self.tasks)} Aufgaben erledigt.", styles["Normal"]))

        doc.build(elements)
        messagebox.showinfo("PDF-Export", f"Exportiert nach:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()
