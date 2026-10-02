import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import random, sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db import get_connection


C = {
    'bg':            '#f1f5f9',
    'sidebar':       '#0f172a',
    'sidebar_hover': '#1e293b',
    'sidebar_act':   '#3b82f6',
    'sidebar_text':  '#cbd5e1',
    'card':          '#ffffff',
    'text':          '#0f172a',
    'muted':         '#64748b',
    'border':        '#e2e8f0',
    'primary':       '#3b82f6',
    'primary_dark':  '#2563eb',
    'success':       '#10b981',
    'warning':       '#f59e0b',
    'danger':        '#ef4444',
    'purple':        '#8b5cf6',
}

def F(size=10, bold=False):
    family = 'Segoe UI' if os.name == 'nt' else 'Helvetica'
    return (family, size, 'bold' if bold else 'normal')

H1, H2, H3 = F(20, True), F(14, True), F(12, True)
BODY, SMALL, BOLD = F(10), F(9), F(10, True)
METRIC = F(24, True)
NAV = F(10, True)


def db_query(sql, params=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        cur.close(); conn.close()


def db_execute(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid or cur.rowcount
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def db_one(sql, params=None):
    rows = db_query(sql, params)
    return rows[0] if rows else None


class Card(tk.Frame):
    def __init__(self, parent, title=None, padx=16, pady=16, **kw):
        super().__init__(parent, bg=C['card'],
                         highlightthickness=1, highlightbackground=C['border'], **kw)
        self.inner = tk.Frame(self, bg=C['card'])
        self.inner.pack(fill='both', expand=True, padx=padx, pady=pady)
        if title:
            tk.Label(self.inner, text=title, font=H3,
                     bg=C['card'], fg=C['text']).pack(anchor='w', pady=(0, 10))


class Btn(tk.Button):
    def __init__(self, parent, text, command=None, kind='primary', **kw):
        palette = {
            'primary': (C['primary'], 'white', C['primary_dark']),
            'success': (C['success'], 'white', '#059669'),
            'danger':  (C['danger'],  'white', '#dc2626'),
            'warning': (C['warning'], 'white', '#d97706'),
            'ghost':   (C['bg'],      C['text'], C['border']),
        }
        bg, fg, active = palette.get(kind, palette['primary'])
        super().__init__(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=active, activeforeground=fg,
                         font=BOLD, relief='flat', bd=0, padx=14, pady=8,
                         cursor='hand2', **kw)


def build_table(parent, columns, widths=None, height=14):
    wrap = tk.Frame(parent, bg=C['card'])
    tree = ttk.Treeview(wrap, columns=columns, show='headings', height=height)
    for i, col in enumerate(columns):
        tree.heading(col, text=col)
        w = widths[i] if widths and i < len(widths) else 120
        anchor = 'e' if str(col).lower() in (
            'fee', 'revenue', 'count', 'pax', 'cap', 'km', 'id', 'rating',
            'students', 'trips', 'avg delay', 'max delay', 'paid', 'total') else 'w'
        tree.column(col, width=w, anchor=anchor, stretch=True)
    vsb = ttk.Scrollbar(wrap, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side='left', fill='both', expand=True)
    vsb.pack(side='right', fill='y')
    # Zebra stripes
    tree.tag_configure('odd', background='#f8fafc')
    return wrap, tree


class FormDialog(tk.Toplevel):
    """Modal form with labelled fields."""
    def __init__(self, parent, title, fields, initial=None, on_submit=None):
        super().__init__(parent)
        self.title(title); self.configure(bg=C['bg'])
        self.resizable(False, False); self.transient(parent); self.grab_set()
        self.result = None; self.on_submit = on_submit
        self.field_widgets = {}; self.initial = initial or {}

        wrap = tk.Frame(self, bg=C['bg'])
        wrap.pack(fill='both', expand=True, padx=24, pady=20)
        tk.Label(wrap, text=title, font=H2, bg=C['bg']).pack(anchor='w', pady=(0, 14))

        for spec in fields:
            name, label = spec['name'], spec['label']
            kind = spec.get('type', 'text')
            opts = spec.get('options', [])
            req = spec.get('required', False)

            tk.Label(wrap, text=label + (' *' if req else ''), font=SMALL,
                     bg=C['bg'], fg=C['muted']).pack(anchor='w', pady=(6, 2))

            if kind == 'choice':
                var = tk.StringVar(value=str(self.initial.get(name, opts[0] if opts else '')))
                w = ttk.Combobox(wrap, textvariable=var, values=opts,
                                 state='readonly', width=40)
            else:
                init = self.initial.get(name, '')
                var = tk.StringVar(value='' if init is None else str(init))
                w = ttk.Entry(wrap, textvariable=var, width=42)

            w.pack(fill='x', ipady=4)
            self.field_widgets[name] = (var, kind, req)

        btns = tk.Frame(wrap, bg=C['bg'])
        btns.pack(fill='x', pady=(20, 0))
        Btn(btns, "Cancel", self.destroy, 'ghost').pack(side='right')
        Btn(btns, "Save", self._submit, 'primary').pack(side='right', padx=(0, 8))

        self.bind('<Return>', lambda e: self._submit())
        self.bind('<Escape>', lambda e: self.destroy())
        self.update_idletasks()
        self._center(parent)

    def _center(self, parent):
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w)//2}+{py + (ph - h)//2}")

    def _submit(self):
        data = {}
        for name, (var, kind, req) in self.field_widgets.items():
            v = var.get().strip()
            if req and not v:
                messagebox.showwarning("Required", f"'{name}' is required.", parent=self); return
            if kind == 'number' and v:
                try:
                    v = float(v) if '.' in v else int(v)
                except ValueError:
                    messagebox.showwarning("Invalid", f"'{name}' must be a number.", parent=self); return
            data[name] = v if v != '' else None
        self.result = data
        if self.on_submit:
            try:
                self.on_submit(data)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self); return
        self.destroy()



class BaseFrame(tk.Frame):
    title = "Page"
    subtitle = ""

    def __init__(self, parent, app):
        super().__init__(parent, bg=C['bg'])
        self.app = app
        head = tk.Frame(self, bg=C['bg'])
        head.pack(fill='x', padx=24, pady=(20, 16))
        tk.Label(head, text=self.title, font=H1,
                 bg=C['bg'], fg=C['text']).pack(anchor='w')
        if self.subtitle:
            tk.Label(head, text=self.subtitle, font=BODY,
                     bg=C['bg'], fg=C['muted']).pack(anchor='w')
        self.body = tk.Frame(self, bg=C['bg'])
        self.body.pack(fill='both', expand=True, padx=24, pady=(0, 24))
        self.build()

    def build(self): pass
    def refresh(self): pass


class DashboardFrame(BaseFrame):
    title = "Dashboard"
    subtitle = "Live overview of the shuttle service"

    def build(self):
        row = tk.Frame(self.body, bg=C['bg']); row.pack(fill='x', pady=(0, 16))
        self.metrics = {}
        for key, label, icon, color in [
            ('persons',  'People',        '👥', C['primary']),
            ('routes',   'Active Routes', '🛣️', C['success']),
            ('shuttles', 'Shuttles',      '🚌', C['warning']),
            ('regs',     'Registrations', '📝', C['purple']),
            ('revenue',  'Revenue (BDT)', '💰', C['danger']),
        ]:
            card = tk.Frame(row, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
            card.pack(side='left', fill='x', expand=True, padx=(0, 10))
            tk.Label(card, text=icon, font=('Segoe UI Emoji', 18),
                     bg=C['card']).pack(anchor='w', padx=14, pady=(12, 0))
            tk.Label(card, text=label, font=SMALL,
                     bg=C['card'], fg=C['muted']).pack(anchor='w', padx=14)
            v = tk.Label(card, text="—", font=METRIC, bg=C['card'], fg=color)
            v.pack(anchor='w', padx=14, pady=(0, 12))
            self.metrics[key] = v

        card = Card(self.body, title="Recent Registrations")
        card.pack(fill='both', expand=True)
        cols = ('ID', 'Student', 'Route', 'Term', 'Fee', 'Payment', 'Status')
        widths = (60, 220, 120, 160, 110, 110, 110)
        wrap, self.tree = build_table(card.inner, cols, widths)
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            self.metrics['persons'].config(
                text=str(db_one("SELECT COUNT(*) c FROM person")['c']))
            self.metrics['routes'].config(
                text=str(db_one("SELECT COUNT(*) c FROM route WHERE is_active=TRUE")['c']))
            self.metrics['shuttles'].config(
                text=str(db_one("SELECT COUNT(*) c FROM shuttle")['c']))
            self.metrics['regs'].config(
                text=str(db_one("SELECT COUNT(*) c FROM student_registration")['c']))
            rev = db_one("""SELECT COALESCE(SUM(fee_charged),0) s
                            FROM student_registration WHERE payment_status='Paid'""")['s']
            self.metrics['revenue'].config(text=f"{float(rev):,.0f}")

            rows = db_query("""
                SELECT sr.registration_id, p.full_name, r.route_code,
                       t.term_name, sr.fee_charged, sr.payment_status, sr.status
                FROM student_registration sr
                JOIN person p ON sr.student_uiu_id = p.uiu_id
                JOIN route r ON sr.route_id = r.route_id
                JOIN term t ON sr.term_id = t.term_id
                ORDER BY sr.registration_id DESC LIMIT 20
            """)
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', tags=('odd',) if i % 2 else (), values=(
                    r['registration_id'], r['full_name'], r['route_code'],
                    r['term_name'], f"{float(r['fee_charged']):,.0f}",
                    r['payment_status'], r['status']))
        except Exception as e:
            print("Dashboard refresh error:", e)


class StudentViewFrame(BaseFrame):
    title = "Student View"
    subtitle = "Look up a student's registration and upcoming buses"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        tk.Label(bar, text="UIU ID:", font=BOLD, bg=C['bg']).pack(side='left')
        self.uiu_var = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.uiu_var, width=20)
        e.pack(side='left', padx=8, ipady=4)
        e.bind('<Return>', lambda ev: self.lookup())
        Btn(bar, "🔍 Look Up", self.lookup, 'primary').pack(side='left')

        self.info_card = Card(self.body, title="Student")
        self.info_card.pack(fill='x', pady=(0, 12))
        self.info = tk.Label(self.info_card.inner, text="—", font=BODY,
                             bg=C['card'], justify='left', anchor='w')
        self.info.pack(fill='x')

        reg_card = Card(self.body, title="Registrations")
        reg_card.pack(fill='x', pady=(0, 12))
        cols = ('Reg ID', 'Route', 'Term', 'Stop', 'Payment', 'Status')
        wrap, self.reg_tree = build_table(reg_card.inner, cols,
                                          (80, 240, 160, 220, 110, 110), height=5)
        wrap.pack(fill='x')

        trip_card = Card(self.body, title="Next Buses")
        trip_card.pack(fill='both', expand=True)
        cols2 = ('Trip', 'Date', 'Time', 'Direction', 'Bus', 'Occupancy')
        wrap2, self.trip_tree = build_table(trip_card.inner, cols2,
                                            (70, 110, 100, 120, 160, 220))
        wrap2.pack(fill='both', expand=True)

    def lookup(self):
        uiu = self.uiu_var.get().strip()
        if not uiu:
            return
        try:
            s = db_one("""SELECT uiu_id, full_name, designation, email, phone
                          FROM person WHERE uiu_id=%s""", (uiu,))
            if not s:
                self.info.config(text=f"❌ No person found with UIU ID '{uiu}'.")
                self.reg_tree.delete(*self.reg_tree.get_children())
                self.trip_tree.delete(*self.trip_tree.get_children())
                return
            self.info.config(text=(
                f"👤  {s['full_name']}  ({s['designation']})\n"
                f"✉   {s['email'] or '—'}\n"
                f"📞  {s['phone'] or '—'}"))

            regs = db_query("""
                SELECT sr.registration_id, r.route_code, r.route_name,
                       t.term_name, st.stop_name, sr.payment_status,
                       sr.status, sr.route_id
                FROM student_registration sr
                JOIN route r ON sr.route_id = r.route_id
                JOIN term t ON sr.term_id = t.term_id
                LEFT JOIN stop st ON sr.boarding_stop_id = st.stop_id
                WHERE sr.student_uiu_id = %s
                ORDER BY sr.registration_date DESC
            """, (uiu,))
            self.reg_tree.delete(*self.reg_tree.get_children())
            paid_route = None
            for i, r in enumerate(regs):
                self.reg_tree.insert('', 'end', tags=('odd',) if i % 2 else (), values=(
                    r['registration_id'],
                    f"{r['route_code']} — {r['route_name']}",
                    r['term_name'], r['stop_name'] or '—',
                    r['payment_status'], r['status']))
                if r['payment_status'] == 'Paid' and r['status'] == 'Active':
                    paid_route = r['route_id']

            self.trip_tree.delete(*self.trip_tree.get_children())
            if not paid_route:
                return
            trips = db_query("""
                SELECT t.trip_id, t.trip_date, s.departure_time, s.direction,
                       sh.registration_no, sh.capacity, t.passenger_count
                FROM trip t
                JOIN schedule s ON t.schedule_id = s.schedule_id
                JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
                WHERE s.route_id = %s AND t.trip_date >= CURDATE()
                  AND t.status <> 'Cancelled'
                ORDER BY t.trip_date, s.departure_time LIMIT 10
            """, (paid_route,))
            for i, t in enumerate(trips):
                cap = t['capacity'] or 1
                pax = t['passenger_count']
                pct = int((pax / cap) * 100)
                bar = '█' * min(pct // 10, 10) + '░' * (10 - min(pct // 10, 10))
                note = ' 🚨 FULL' if pct >= 100 else (' ⚠️' if pct >= 80 else '')
                self.trip_tree.insert('', 'end', tags=('odd',) if i % 2 else (), values=(
                    t['trip_id'], t['trip_date'], str(t['departure_time']),
                    t['direction'], t['registration_no'],
                    f"[{bar}] {pax}/{cap}{note}"))
        except Exception as e:
            messagebox.showerror("Error", str(e))



class PeopleFrame(BaseFrame):
    title = "People"
    subtitle = "Students, faculty, staff, drivers, and admins"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Add", self.add, 'primary').pack(side='left')
        Btn(bar, "✎ Edit", self.edit, 'ghost').pack(side='left', padx=(8, 0))
        Btn(bar, "🗑 Delete", self.delete, 'danger').pack(side='left', padx=(8, 0))
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))
        tk.Label(bar, text="Filter:", font=BOLD, bg=C['bg']).pack(side='left', padx=(24, 6))
        self.filter_var = tk.StringVar(value='All')
        cb = ttk.Combobox(bar, textvariable=self.filter_var, state='readonly',
                          values=['All', 'Student', 'Faculty', 'Staff', 'Driver', 'Admin'],
                          width=12)
        cb.pack(side='left'); cb.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        card = Card(self.body); card.pack(fill='both', expand=True)
        cols = ('UIU ID', 'Full Name', 'Designation', 'Email', 'Phone', 'Address')
        wrap, self.tree = build_table(card.inner, cols, (140, 220, 110, 240, 130, 220))
        wrap.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', lambda e: self.edit())

    def refresh(self):
        f = self.filter_var.get()
        try:
            if f == 'All':
                rows = db_query("SELECT * FROM person ORDER BY designation, uiu_id")
            else:
                rows = db_query("SELECT * FROM person WHERE designation=%s ORDER BY uiu_id", (f,))
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', iid=r['uiu_id'],
                                 tags=('odd',) if i % 2 else (), values=(
                    r['uiu_id'], r['full_name'], r['designation'],
                    r['email'] or '', r['phone'] or '', r['address'] or ''))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _sel(self):
        s = self.tree.selection()
        if not s:
            messagebox.showinfo("Select", "Please select a person.")
            return None
        return s[0]

    def add(self):
        def submit(d):
            db_execute("""INSERT INTO person
                (uiu_id, full_name, designation, email, phone, address)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (d['uiu_id'], d['full_name'], d['designation'],
                 d['email'], d['phone'], d['address']))
        FormDialog(self, "Add Person", [
            {'name':'uiu_id','label':'UIU ID','required':True},
            {'name':'full_name','label':'Full Name','required':True},
            {'name':'designation','label':'Designation','required':True,
             'type':'choice','options':['Student','Faculty','Staff','Driver','Admin']},
            {'name':'email','label':'Email','required':True},
            {'name':'phone','label':'Phone'},
            {'name':'address','label':'Address'},
        ], on_submit=submit)
        self.refresh()

    def edit(self):
        uiu = self._sel()
        if not uiu: return
        row = db_one("SELECT * FROM person WHERE uiu_id=%s", (uiu,))
        if not row: return
        def submit(d):
            db_execute("""UPDATE person SET full_name=%s, designation=%s,
                          email=%s, phone=%s, address=%s WHERE uiu_id=%s""",
                       (d['full_name'], d['designation'], d['email'],
                        d['phone'], d['address'], uiu))
        FormDialog(self, "Edit Person", [
            {'name':'full_name','label':'Full Name','required':True},
            {'name':'designation','label':'Designation','required':True,
             'type':'choice','options':['Student','Faculty','Staff','Driver','Admin']},
            {'name':'email','label':'Email','required':True},
            {'name':'phone','label':'Phone'},
            {'name':'address','label':'Address'},
        ], initial=row, on_submit=submit)
        self.refresh()

    def delete(self):
        uiu = self._sel()
        if not uiu: return
        if not messagebox.askyesno("Confirm",
                f"Delete person '{uiu}'?\nThis cascades to registrations, boarding, feedback, etc."):
            return
        try:
            db_execute("DELETE FROM person WHERE uiu_id=%s", (uiu,))
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))



class RoutesFrame(BaseFrame):
    title = "Routes"
    subtitle = "Manage shuttle routes and per-term fees"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Add", self.add, 'primary').pack(side='left')
        Btn(bar, "✎ Edit", self.edit, 'ghost').pack(side='left', padx=(8, 0))
        Btn(bar, "💰 Set Fee", self.set_fee, 'warning').pack(side='left', padx=(8, 0))
        Btn(bar, "⏸ Deactivate", self.deactivate, 'danger').pack(side='left', padx=(8, 0))
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))

        card = Card(self.body); card.pack(fill='both', expand=True)
        cols = ('ID', 'Code', 'Name', 'Service', 'Km', 'Active', 'Remarks')
        wrap, self.tree = build_table(card.inner, cols, (50, 110, 260, 130, 70, 70, 220))
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            rows = db_query("""SELECT route_id, route_code, route_name, service_type,
                                      distance_km, is_active, remarks
                               FROM route ORDER BY route_code""")
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', iid=r['route_id'],
                                 tags=('odd',) if i % 2 else (), values=(
                    r['route_id'], r['route_code'], r['route_name'],
                    r['service_type'], r['distance_km'] or '',
                    'Yes' if r['is_active'] else 'No', r['remarks'] or ''))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _sel(self):
        s = self.tree.selection()
        if not s:
            messagebox.showinfo("Select", "Select a route first."); return None
        return int(s[0])

    def add(self):
        def submit(d):
            db_execute("""INSERT INTO route
                (route_code, route_name, service_type, start_stop_id,
                 end_stop_id, distance_km, remarks)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (d['route_code'], d['route_name'], d['service_type'],
                 d['start_stop_id'], d['end_stop_id'], d['distance_km'], d['remarks']))
        FormDialog(self, "Add Route", [
            {'name':'route_code','label':'Route Code','required':True},
            {'name':'route_name','label':'Route Name','required':True},
            {'name':'service_type','label':'Service Type','required':True,
             'type':'choice','options':['ShortShuttle','RouteService','FacultyStaff']},
            {'name':'start_stop_id','label':'Start Stop ID','type':'number'},
            {'name':'end_stop_id','label':'End Stop ID','type':'number'},
            {'name':'distance_km','label':'Distance (km)','type':'number'},
            {'name':'remarks','label':'Remarks'},
        ], on_submit=submit)
        self.refresh()

    def edit(self):
        rid = self._sel()
        if not rid: return
        row = db_one("SELECT * FROM route WHERE route_id=%s", (rid,))
        def submit(d):
            db_execute("""UPDATE route SET route_name=%s, remarks=%s,
                          is_active=%s WHERE route_id=%s""",
                       (d['route_name'], d['remarks'],
                        d['is_active'] == 'Yes', rid))
        init = dict(row); init['is_active'] = 'Yes' if row['is_active'] else 'No'
        FormDialog(self, "Edit Route", [
            {'name':'route_name','label':'Route Name','required':True},
            {'name':'remarks','label':'Remarks'},
            {'name':'is_active','label':'Active','type':'choice','options':['Yes','No']},
        ], initial=init, on_submit=submit)
        self.refresh()

    def set_fee(self):
        rid = self._sel()
        if not rid: return
        existing = {r['term_type']: r['fee_amount']
                    for r in db_query("SELECT * FROM route_fee WHERE route_id=%s", (rid,))}
        def submit(d):
            for t, amount in (('Trimester', d['trimester']), ('Semester', d['semester'])):
                if amount is None: continue
                db_execute("""INSERT INTO route_fee (route_id, term_type, fee_amount)
                              VALUES (%s, %s, %s) AS new
                              ON DUPLICATE KEY UPDATE fee_amount = new.fee_amount""",
                           (rid, t, amount))
        FormDialog(self, "Set Route Fee", [
            {'name':'trimester','label':'Trimester Fee (BDT)','type':'number'},
            {'name':'semester','label':'Semester Fee (BDT)','type':'number'},
        ], initial={'trimester': existing.get('Trimester', ''),
                    'semester':  existing.get('Semester', '')},
           on_submit=submit)
        self.refresh()

    def deactivate(self):
        rid = self._sel()
        if not rid: return
        if messagebox.askyesno("Confirm", "Deactivate this route?"):
            db_execute("UPDATE route SET is_active=FALSE WHERE route_id=%s", (rid,))
            self.refresh()



class StopsFrame(BaseFrame):
    title = "Stops"
    subtitle = "Boarding points on routes"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Add", self.add, 'primary').pack(side='left')
        Btn(bar, "🗑 Delete", self.delete, 'danger').pack(side='left', padx=(8, 0))
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))
        card = Card(self.body); card.pack(fill='both', expand=True)
        wrap, self.tree = build_table(card.inner,
            ('ID', 'Stop Name', 'Area', 'Latitude', 'Longitude'),
            (60, 260, 200, 120, 120))
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            rows = db_query("SELECT * FROM stop ORDER BY area, stop_name")
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', iid=r['stop_id'],
                                 tags=('odd',) if i % 2 else (), values=(
                    r['stop_id'], r['stop_name'], r['area'] or '',
                    r['latitude'] or '', r['longitude'] or ''))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add(self):
        def submit(d):
            db_execute("""INSERT INTO stop (stop_name, area, latitude, longitude)
                          VALUES (%s,%s,%s,%s)""",
                       (d['stop_name'], d['area'], d['latitude'], d['longitude']))
        FormDialog(self, "Add Stop", [
            {'name':'stop_name','label':'Stop Name','required':True},
            {'name':'area','label':'Area'},
            {'name':'latitude','label':'Latitude','type':'number'},
            {'name':'longitude','label':'Longitude','type':'number'},
        ], on_submit=submit)
        self.refresh()

    def delete(self):
        s = self.tree.selection()
        if not s: return
        if messagebox.askyesno("Confirm", f"Delete stop ID {s[0]}?"):
            try:
                db_execute("DELETE FROM stop WHERE stop_id=%s", (int(s[0]),))
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))


class ShuttlesFrame(BaseFrame):
    title = "Shuttles"
    subtitle = "Fleet inventory and status"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Add", self.add, 'primary').pack(side='left')
        Btn(bar, "✎ Status", self.status, 'warning').pack(side='left', padx=(8, 0))
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))
        card = Card(self.body); card.pack(fill='both', expand=True)
        wrap, self.tree = build_table(card.inner,
            ('ID', 'Reg No', 'Type', 'Capacity', 'Service', 'Status'),
            (60, 180, 110, 90, 150, 120))
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            rows = db_query("SELECT * FROM shuttle ORDER BY shuttle_id")
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', iid=r['shuttle_id'],
                                 tags=('odd',) if i % 2 else (), values=(
                    r['shuttle_id'], r['registration_no'], r['shuttle_type'],
                    r['capacity'], r['service_type'], r['status']))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add(self):
        def submit(d):
            db_execute("""INSERT INTO shuttle
                (registration_no, shuttle_type, capacity, service_type)
                VALUES (%s,%s,%s,%s)""",
                (d['registration_no'], d['shuttle_type'],
                 d['capacity'], d['service_type']))
        FormDialog(self, "Add Shuttle", [
            {'name':'registration_no','label':'Registration No','required':True},
            {'name':'shuttle_type','label':'Type','required':True,
             'type':'choice','options':['Bus','Minibus','Microbus']},
            {'name':'capacity','label':'Capacity','required':True,'type':'number'},
            {'name':'service_type','label':'Service','required':True,
             'type':'choice','options':['RouteService','ShortShuttle','FacultyStaff']},
        ], on_submit=submit)
        self.refresh()

    def status(self):
        s = self.tree.selection()
        if not s: return
        sid = int(s[0])
        def submit(d):
            db_execute("UPDATE shuttle SET status=%s WHERE shuttle_id=%s",
                       (d['status'], sid))
        FormDialog(self, "Update Status", [
            {'name':'status','label':'Status','type':'choice',
             'options':['Active','Maintenance','Retired']},
        ], on_submit=submit)
        self.refresh()



class SchedulesFrame(BaseFrame):
    title = "Schedules"
    subtitle = "Recurring trips for each route"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Add", self.add, 'primary').pack(side='left')
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))
        card = Card(self.body); card.pack(fill='both', expand=True)
        wrap, self.tree = build_table(card.inner,
            ('ID', 'Route', 'Bus', 'Driver', 'Direction', 'Dep', 'Arr', 'Days'),
            (50, 110, 180, 140, 100, 90, 90, 110))
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            rows = db_query("""
                SELECT s.schedule_id, r.route_code, sh.registration_no,
                       s.driver_uiu_id, s.direction, s.departure_time,
                       s.arrival_time, s.operating_days
                FROM schedule s
                JOIN route r ON s.route_id = r.route_id
                JOIN shuttle sh ON s.shuttle_id = sh.shuttle_id
                ORDER BY r.route_code, s.departure_time
            """)
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', iid=r['schedule_id'],
                                 tags=('odd',) if i % 2 else (), values=(
                    r['schedule_id'], r['route_code'], r['registration_no'],
                    r['driver_uiu_id'] or '', r['direction'],
                    str(r['departure_time']), str(r['arrival_time'] or ''),
                    r['operating_days']))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add(self):
        def submit(d):
            db_execute("""INSERT INTO schedule
                (route_id, shuttle_id, driver_uiu_id, term_id, direction,
                 departure_time, arrival_time, operating_days)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'Mon-Fri')""",
                (d['route_id'], d['shuttle_id'], d['driver_uiu_id'],
                 d['term_id'], d['direction'],
                 d['departure_time'], d['arrival_time']))
        FormDialog(self, "Add Schedule", [
            {'name':'route_id','label':'Route ID','required':True,'type':'number'},
            {'name':'shuttle_id','label':'Shuttle ID','required':True,'type':'number'},
            {'name':'driver_uiu_id','label':'Driver UIU ID'},
            {'name':'term_id','label':'Term ID','required':True,'type':'number'},
            {'name':'direction','label':'Direction','required':True,
             'type':'choice','options':['INBOUND','OUTBOUND']},
            {'name':'departure_time','label':'Departure (HH:MM:SS)','required':True},
            {'name':'arrival_time','label':'Arrival (HH:MM:SS)'},
        ], on_submit=submit)
        self.refresh()



class RegistrationsFrame(BaseFrame):
    title = "Registrations"
    subtitle = "Student subscriptions and payment processing"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Register Student", self.register, 'primary').pack(side='left')
        Btn(bar, "💳 Process Payment", self.pay, 'success').pack(side='left', padx=(8, 0))
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))
        card = Card(self.body); card.pack(fill='both', expand=True)
        wrap, self.tree = build_table(card.inner,
            ('ID', 'Student', 'UIU ID', 'Route', 'Term', 'Fee', 'Payment', 'Status'),
            (60, 200, 130, 110, 140, 100, 100, 100))
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            rows = db_query("""
                SELECT sr.registration_id, p.full_name, p.uiu_id, r.route_code,
                       t.term_name, sr.fee_charged, sr.payment_status, sr.status
                FROM student_registration sr
                JOIN person p ON sr.student_uiu_id = p.uiu_id
                JOIN route r ON sr.route_id = r.route_id
                JOIN term t ON sr.term_id = t.term_id
                ORDER BY sr.registration_id DESC LIMIT 100
            """)
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                self.tree.insert('', 'end', iid=r['registration_id'],
                                 tags=('odd',) if i % 2 else (), values=(
                    r['registration_id'], r['full_name'], r['uiu_id'],
                    r['route_code'], r['term_name'],
                    f"{float(r['fee_charged']):,.0f}",
                    r['payment_status'], r['status']))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def register(self):
        RegisterWizard(self)
        self.refresh()

    def pay(self):
        s = self.tree.selection()
        if not s:
            messagebox.showinfo("Select", "Select a registration to pay.")
            return
        reg_id = int(s[0])
        reg = db_one("""SELECT sr.*, p.full_name FROM student_registration sr
                        JOIN person p ON sr.student_uiu_id = p.uiu_id
                        WHERE sr.registration_id=%s""", (reg_id,))
        if reg['payment_status'] != 'Pending':
            messagebox.showinfo("Info", f"Already {reg['payment_status']}."); return
        if not messagebox.askyesno("Confirm",
                f"Charge {reg['full_name']} {reg['fee_charged']} BDT?"):
            return
        if random.random() < 0.95:
            db_execute("""UPDATE student_registration
                          SET payment_status='Paid', payment_date=CURDATE()
                          WHERE registration_id=%s""", (reg_id,))
            txn = f"TXN-{random.randint(100000,999999)}"
            messagebox.showinfo("Success", f"Payment successful!\nTxn: {txn}")
        else:
            messagebox.showerror("Failed", "Payment gateway declined.")
        self.refresh()


class RegisterWizard(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Register Student"); self.configure(bg=C['bg'])
        self.transient(parent); self.grab_set(); self.resizable(False, False)
        wrap = tk.Frame(self, bg=C['bg']); wrap.pack(fill='both', expand=True, padx=24, pady=20)
        tk.Label(wrap, text="Register a Student", font=H2, bg=C['bg']).pack(anchor='w', pady=(0, 14))

        self.uiu = self._field(wrap, "UIU ID")
        self.term_type = self._choice(wrap, "Term Type", ['Trimester','Semester'])
        self.route_id = self._field(wrap, "Route ID (see routes list)")
        self.stop_id = self._field(wrap, "Boarding Stop ID")

        btns = tk.Frame(wrap, bg=C['bg']); btns.pack(fill='x', pady=(20, 0))
        Btn(btns, "Cancel", self.destroy, 'ghost').pack(side='right')
        Btn(btns, "Register", self._submit, 'primary').pack(side='right', padx=(0, 8))
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (parent.winfo_width()-w)//2}+{py + (parent.winfo_height()-h)//2}")

    def _field(self, parent, label, **kw):
        tk.Label(parent, text=label, font=SMALL, bg=C['bg'], fg=C['muted']).pack(anchor='w', pady=(6,2))
        v = tk.StringVar(); e = ttk.Entry(parent, textvariable=v, width=40); e.pack(fill='x', ipady=4)
        return v

    def _choice(self, parent, label, opts):
        tk.Label(parent, text=label, font=SMALL, bg=C['bg'], fg=C['muted']).pack(anchor='w', pady=(6,2))
        v = tk.StringVar(value=opts[0])
        ttk.Combobox(parent, textvariable=v, values=opts, state='readonly', width=38).pack(fill='x', ipady=4)
        return v

    def _submit(self):
        uiu = self.uiu.get().strip()
        if not uiu:
            messagebox.showwarning("Required", "UIU ID is required.", parent=self); return
        try:
            # Ensure student exists
            if not db_one("SELECT 1 FROM person WHERE uiu_id=%s AND designation='Student'", (uiu,)):
                messagebox.showerror("Not Found",
                    "Student doesn't exist. Add them in 'People' first.", parent=self); return
            term = db_one("""SELECT * FROM term WHERE term_type=%s
                             ORDER BY start_date DESC LIMIT 1""", (self.term_type.get(),))
            if not term:
                messagebox.showerror("Missing",
                    f"No {self.term_type.get()} term defined.", parent=self); return
            rid = int(self.route_id.get())
            fee = db_one("""SELECT fee_amount FROM route_fee
                            WHERE route_id=%s AND term_type=%s""",
                         (rid, term['term_type']))
            if not fee:
                messagebox.showerror("Missing", "No fee defined for this route/term.", parent=self); return
            stop_id = int(self.stop_id.get()) if self.stop_id.get().strip() else None
            db_execute("""INSERT INTO student_registration
                (student_uiu_id, route_id, term_id, boarding_stop_id,
                 fee_charged, payment_status, status)
                VALUES (%s,%s,%s,%s,%s,'Pending','Active')""",
                (uiu, rid, term['term_id'], stop_id, fee['fee_amount']))
            messagebox.showinfo("Success", "Registration created.", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)


# ═══════════════════════════════════════════════════════════
# CARD PUNCH
# ═══════════════════════════════════════════════════════════
class CardPunchFrame(BaseFrame):
    title = "Card Punch"
    subtitle = "Simulate a student tapping their card to board"

    def build(self):
        # ── Toolbar inside a Card ──
        bar_card = Card(self.body)
        bar_card.pack(fill='x', pady=(0, 12))
        bar = bar_card.inner

        tk.Label(bar, text="UIU ID:", font=BOLD, bg=C['card']).pack(side='left')
        self.uiu = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.uiu, width=22)
        e.pack(side='left', padx=8, ipady=4)
        e.bind('<Return>', lambda ev: self.load_trips())
        Btn(bar, "💳 Look Up Card", self.load_trips, 'primary').pack(side='left')
        Btn(bar, "🎫 Punch In", self.punch, 'success').pack(side='left', padx=(8, 0))
        Btn(bar, "⟳ Refresh", self.load_trips, 'ghost').pack(side='left', padx=(8, 0))

        # ── Person info ──
        info_card = Card(self.body, title="Person")
        info_card.pack(fill='x', pady=(0, 12))
        self.info = tk.Label(info_card.inner, text="—", font=BODY,
                             bg=C['card'], justify='left', anchor='w')
        self.info.pack(fill='x')

        # ── Trips table ──
        trip_card = Card(self.body, title="Available Trips (latest date)")
        trip_card.pack(fill='both', expand=True)
        wrap, self.tree = build_table(
            trip_card.inner,
            ('Trip', 'Route', 'Direction', 'Dep', 'Bus', 'Cap', 'Occupancy'),
            (60, 120, 100, 100, 170, 70, 220))
        wrap.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', lambda e: self.punch())
        # Highlight already-boarded rows in a muted color
        self.tree.tag_configure('boarded', foreground=C['muted'])


    def load_trips(self):
        uiu = self.uiu.get().strip()
        if not uiu:
            self.info.config(text="Enter a UIU ID and press Look Up.")
            self.tree.delete(*self.tree.get_children())
            return
        p = db_one("SELECT * FROM person WHERE uiu_id=%s", (uiu,))
        if not p:
            self.info.config(text=f"❌ Card not recognized: {uiu}")
            self.tree.delete(*self.tree.get_children())
            return
        self.info.config(text=f"👤  {p['full_name']}  ({p['designation']})")

        # Scope to the person's eligible route(s) when we can
        eligible_route = None
        if p['designation'] == 'Student':
            row = db_one("""SELECT route_id FROM student_registration
                            WHERE student_uiu_id=%s AND status='Active'
                              AND payment_status='Paid'
                            ORDER BY registration_date DESC LIMIT 1""", (uiu,))
            if row:
                eligible_route = row['route_id']
        elif p['designation'] in ('Faculty', 'Staff'):
            row = db_one("""SELECT route_id FROM faculty_authorization
                            WHERE person_uiu_id=%s AND is_active=TRUE
                            ORDER BY authorized_from DESC LIMIT 1""", (uiu,))
            if row:
                eligible_route = row['route_id']

        sql = """
            SELECT t.trip_id, r.route_code, r.route_id, s.direction,
                   s.departure_time, sh.capacity, sh.registration_no,
                   t.passenger_count
            FROM trip t
            JOIN schedule s ON t.schedule_id = s.schedule_id
            JOIN route r ON s.route_id = r.route_id
            JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
            WHERE t.trip_date = (SELECT MAX(trip_date) FROM trip)
              AND t.status <> 'Cancelled'
        """
        params = ()
        if eligible_route:
            sql += " AND r.route_id = %s "
            params = (eligible_route,)
        sql += " ORDER BY t.trip_id LIMIT 30"

        try:
            rows = db_query(sql, params)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        self.tree.delete(*self.tree.get_children())
        boarded = set()
        for r in db_query("SELECT trip_id FROM trip_passenger WHERE person_uiu_id=%s", (uiu,)):
            boarded.add(r['trip_id'])

        for i, r in enumerate(rows):
            already = r['trip_id'] in boarded
            tag = 'boarded' if already else ('odd' if i % 2 else '')
            occ = f"{r['passenger_count']}/{r['capacity']}"
            if already:
                occ += "  ✅ boarded"
            self.tree.insert('', 'end', iid=r['trip_id'], tags=(tag,) if tag else (), values=(
                r['trip_id'], r['route_code'], r['direction'],
                str(r['departure_time']), r['registration_no'],
                r['capacity'], occ))


    def refresh(self):
        if self.uiu.get().strip():
            self.load_trips()

    # ── Punch ──
    def punch(self):
        uiu = self.uiu.get().strip()
        if not uiu:
            messagebox.showinfo("Missing", "Enter a UIU ID first."); return
        s = self.tree.selection()
        if not s:
            messagebox.showinfo("Select", "Select a trip from the list."); return
        trip_id = int(s[0])
        try:
            trip = db_one("""
                SELECT t.passenger_count, sh.capacity, r.service_type,
                       r.route_id, s.direction
                FROM trip t
                JOIN schedule s ON t.schedule_id = s.schedule_id
                JOIN route r ON s.route_id = r.route_id
                JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
                WHERE t.trip_id = %s
            """, (trip_id,))
            if not trip:
                messagebox.showerror("Error", "Trip not found."); return
            if trip['passenger_count'] >= trip['capacity']:
                messagebox.showwarning("Full", "Trip is already full."); return
            if db_one("""SELECT 1 FROM trip_passenger
                         WHERE trip_id=%s AND person_uiu_id=%s""", (trip_id, uiu)):
                messagebox.showinfo("Duplicate", "This person already boarded."); return

            btype = 'WalkOn'
            if trip['service_type'] == 'ShortShuttle':
                btype = 'Free'
            elif trip['service_type'] == 'FacultyStaff':
                if not db_one("""SELECT 1 FROM faculty_authorization
                                 WHERE person_uiu_id=%s AND route_id=%s
                                   AND is_active=TRUE""",
                              (uiu, trip['route_id'])):
                    messagebox.showerror("Unauthorized",
                        "Not authorized for the faculty bus."); return
                btype = 'Free'
            elif trip['service_type'] == 'RouteService':
                if db_one("""SELECT 1 FROM student_registration
                             WHERE student_uiu_id=%s AND route_id=%s
                               AND status='Active' AND payment_status='Paid'""",
                          (uiu, trip['route_id'])):
                    btype = 'Registered'

            stop = db_one("""SELECT stop_id FROM route_stop
                             WHERE route_id=%s AND direction=%s
                             ORDER BY stop_order LIMIT 1""",
                          (trip['route_id'], trip['direction']))
            if not stop:
                messagebox.showerror("Error", "No stops on this route."); return

            db_execute("""INSERT INTO trip_passenger
                          (trip_id, person_uiu_id, stop_id, boarding_type)
                          VALUES (%s,%s,%s,%s)""",
                       (trip_id, uiu, stop['stop_id'], btype))

            upd = db_one("""SELECT passenger_count, departure_signal_sent
                            FROM trip WHERE trip_id=%s""", (trip_id,))
            msg = f"✅ Boarded ({btype}).\nOnboard: {upd['passenger_count']}/{trip['capacity']}"
            if upd['departure_signal_sent']:
                msg += "\n🚨 Bus is FULL — driver notified."
            messagebox.showinfo("Success", msg)
            self.load_trips()
        except Exception as e:
            messagebox.showerror("Error", str(e))

class ReportsFrame(BaseFrame):
    title = "Reports"
    subtitle = "Analytics across revenue, occupancy, delays, and feedback"

    def build(self):
        nb = ttk.Notebook(self.body)
        nb.pack(fill='both', expand=True)
        self.tabs = {}
        for name, builder in [
            ('Revenue',    self._rev),
            ('Overcrowded', self._over),
            ('Never Boarded', self._nb_rep),
            ('Delay',      self._delay),
            ('Complaints', self._complaints),
            ('Feedback',   self._feedback),
        ]:
            frame = tk.Frame(nb, bg=C['bg'])
            nb.add(frame, text=name)
            self.tabs[name] = frame
            builder(frame)

    def _mk(self, parent, cols, widths, height=14):
        card = Card(parent); card.pack(fill='both', expand=True, padx=12, pady=12)
        wrap, tree = build_table(card.inner, cols, widths, height=height)
        wrap.pack(fill='both', expand=True)
        return tree

    def _rev(self, p):
        self.rev_tree = self._mk(p, ('Route', 'Name', 'Students', 'Revenue (BDT)'),
                                 (110, 300, 100, 160))
    def _over(self, p):
        self.over_tree = self._mk(p, ('Trip', 'Date', 'Route', 'Pax', 'Capacity'),
                                  (70, 120, 110, 80, 100))
    def _nb_rep(self, p):
        self.nb_tree = self._mk(p, ('UIU ID', 'Name', 'Route', 'Paid (BDT)'),
                                (130, 240, 120, 120))
    def _delay(self, p):
        self.delay_tree = self._mk(p, ('Route', 'Trips', 'Avg (min)', 'Max (min)'),
                                   (120, 90, 110, 110))
    def _complaints(self, p):
        self.comp_tree = self._mk(p, ('Category', 'Total', 'Resolved'),
                                  (180, 100, 120))
    def _feedback(self, p):
        self.fb_tree = self._mk(p, ('Route', 'Avg Rating', 'Feedbacks'),
                                (140, 130, 120))

    def refresh(self):
        try:
            for t in self.rev_tree.get_children(): self.rev_tree.delete(t)
            for i, r in enumerate(db_query("""
                SELECT r.route_code, r.route_name,
                       COUNT(sr.registration_id) c,
                       COALESCE(SUM(sr.fee_charged),0) s
                FROM route r LEFT JOIN student_registration sr
                  ON r.route_id = sr.route_id AND sr.payment_status='Paid'
                WHERE r.service_type='RouteService'
                GROUP BY r.route_id ORDER BY s DESC""")):
                self.rev_tree.insert('', 'end', tags=('odd',) if i%2 else (), values=(
                    r['route_code'], r['route_name'], r['c'], f"{float(r['s']):,.0f}"))

            for t in self.over_tree.get_children(): self.over_tree.delete(t)
            for i, r in enumerate(db_query("""
                SELECT t.trip_id, t.trip_date, r.route_code, t.passenger_count, sh.capacity
                FROM trip t JOIN schedule s ON t.schedule_id=s.schedule_id
                JOIN route r ON s.route_id=r.route_id
                JOIN shuttle sh ON t.shuttle_id=sh.shuttle_id
                WHERE t.passenger_count > sh.capacity
                ORDER BY t.trip_date DESC LIMIT 50""")):
                self.over_tree.insert('', 'end', tags=('odd',) if i%2 else (), values=(
                    r['trip_id'], r['trip_date'], r['route_code'],
                    r['passenger_count'], r['capacity']))

            for t in self.nb_tree.get_children(): self.nb_tree.delete(t)
            for i, r in enumerate(db_query("""
                SELECT p.uiu_id, p.full_name, r.route_code, sr.fee_charged
                FROM student_registration sr
                JOIN person p ON sr.student_uiu_id=p.uiu_id
                JOIN route r ON sr.route_id=r.route_id
                WHERE sr.status='Active' AND sr.payment_status='Paid'
                  AND NOT EXISTS (
                    SELECT 1 FROM trip_passenger tp
                    JOIN trip t ON tp.trip_id=t.trip_id
                    JOIN schedule sc ON t.schedule_id=sc.schedule_id
                    WHERE tp.person_uiu_id=sr.student_uiu_id
                      AND sc.route_id=sr.route_id)
                ORDER BY sr.fee_charged DESC""")):
                self.nb_tree.insert('', 'end', tags=('odd',) if i%2 else (), values=(
                    r['uiu_id'], r['full_name'], r['route_code'],
                    f"{float(r['fee_charged']):,.0f}"))

            for t in self.delay_tree.get_children(): self.delay_tree.delete(t)
            for i, r in enumerate(db_query("""
                SELECT r.route_code, COUNT(*) c,
                       ROUND(AVG(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure),
                            s.departure_time)))/60,1) avg_d,
                       MAX(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure),
                            s.departure_time))/60) max_d
                FROM trip t JOIN schedule s ON t.schedule_id=s.schedule_id
                JOIN route r ON s.route_id=r.route_id
                WHERE t.actual_departure IS NOT NULL AND t.status<>'Cancelled'
                GROUP BY r.route_id ORDER BY avg_d DESC""")):
                self.delay_tree.insert('', 'end', tags=('odd',) if i%2 else (), values=(
                    r['route_code'], r['c'],
                    f"{float(r['avg_d'] or 0):.1f}",
                    f"{float(r['max_d'] or 0):.0f}"))

            for t in self.comp_tree.get_children(): self.comp_tree.delete(t)
            for i, r in enumerate(db_query("""
                SELECT category, COUNT(*) c,
                       SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) r
                FROM complaint GROUP BY category ORDER BY c DESC""")):
                self.comp_tree.insert('', 'end', tags=('odd',) if i%2 else (), values=(
                    r['category'], r['c'], int(r['r'] or 0)))

            for t in self.fb_tree.get_children(): self.fb_tree.delete(t)
            for i, r in enumerate(db_query("""
                SELECT r.route_code, ROUND(AVG(f.rating),2) a, COUNT(*) c
                FROM feedback f
                JOIN trip t ON f.trip_id=t.trip_id
                JOIN schedule s ON t.schedule_id=s.schedule_id
                JOIN route r ON s.route_id=r.route_id
                GROUP BY r.route_code ORDER BY a DESC""")):
                self.fb_tree.insert('', 'end', tags=('odd',) if i%2 else (), values=(
                    r['route_code'], float(r['a']), r['c']))
        except Exception as e:
            print("Reports refresh error:", e)



class FeedbackFrame(BaseFrame):
    title = "Feedback"
    subtitle = "Submit and review student trip feedback"

    def build(self):
        bar = tk.Frame(self.body, bg=C['bg']); bar.pack(fill='x', pady=(0, 12))
        Btn(bar, "+ Submit Feedback", self.submit, 'primary').pack(side='left')
        Btn(bar, "⟳ Refresh", self.refresh, 'ghost').pack(side='left', padx=(8, 0))
        card = Card(self.body, title="Recent Feedback")
        card.pack(fill='both', expand=True)
        wrap, self.tree = build_table(card.inner,
            ('ID', 'Student', 'Trip', 'Rating', 'Comment', 'When'),
            (60, 200, 80, 100, 360, 160))
        wrap.pack(fill='both', expand=True)

    def refresh(self):
        try:
            rows = db_query("""
                SELECT f.feedback_id, p.full_name, f.trip_id,
                       f.rating, f.comment, f.created_at
                FROM feedback f
                JOIN person p ON f.person_uiu_id=p.uiu_id
                ORDER BY f.created_at DESC LIMIT 100
            """)
            self.tree.delete(*self.tree.get_children())
            for i, r in enumerate(rows):
                stars = '⭐' * int(r['rating'])
                self.tree.insert('', 'end', iid=r['feedback_id'],
                                 tags=('odd',) if i%2 else (), values=(
                    r['feedback_id'], r['full_name'], r['trip_id'],
                    stars, r['comment'] or '', str(r['created_at'])))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def submit(self):
        def do(d):
            uiu = d['uiu_id']; trip_id = int(d['trip_id']); rating = int(d['rating'])
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be 1–5.")
            if not db_one("SELECT 1 FROM person WHERE uiu_id=%s", (uiu,)):
                raise ValueError("Person not found.")
            if not db_one("""SELECT 1 FROM trip_passenger
                             WHERE person_uiu_id=%s AND trip_id=%s""", (uiu, trip_id)):
                raise ValueError("This person hasn't boarded that trip.")
            if db_one("""SELECT 1 FROM feedback
                         WHERE person_uiu_id=%s AND trip_id=%s""", (uiu, trip_id)):
                raise ValueError("Feedback already submitted for this trip.")
            db_execute("""INSERT INTO feedback
                          (person_uiu_id, trip_id, rating, comment)
                          VALUES (%s,%s,%s,%s)""",
                       (uiu, trip_id, rating, d['comment']))
        FormDialog(self, "Submit Feedback", [
            {'name':'uiu_id','label':'Student UIU ID','required':True},
            {'name':'trip_id','label':'Trip ID','required':True,'type':'number'},
            {'name':'rating','label':'Rating (1–5)','required':True,'type':'number'},
            {'name':'comment','label':'Comment'},
        ], on_submit=do)
        self.refresh()



FRAME_REGISTRY = {
    'dashboard': DashboardFrame,
    'student':   StudentViewFrame,
    'people':    PeopleFrame,
    'routes':    RoutesFrame,
    'stops':     StopsFrame,
    'shuttles':  ShuttlesFrame,
    'schedules': SchedulesFrame,
    'register':  RegistrationsFrame,
    'punch':     CardPunchFrame,
    'reports':   ReportsFrame,
    'feedback':  FeedbackFrame,
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UIU Shuttle Management System")
        self.geometry("1300x820"); self.minsize(1100, 700)
        self.configure(bg=C['bg'])
        self._style()
        self._layout()
        self.after(50, lambda: self._show('dashboard'))

    def _style(self):
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('Treeview', background='white', fieldbackground='white',
                    foreground=C['text'], rowheight=30, borderwidth=0, font=BODY)
        s.configure('Treeview.Heading', background=C['bg'], foreground=C['muted'],
                    font=BOLD, borderwidth=0, relief='flat', padding=(8, 8))
        s.map('Treeview', background=[('selected', C['primary'])],
              foreground=[('selected', 'white')])
        s.map('Treeview.Heading', background=[('active', C['border'])])
        s.configure('TNotebook', background=C['bg'], borderwidth=0)
        s.configure('TNotebook.Tab', padding=(16, 8), font=BOLD,
                    background=C['bg'], foreground=C['muted'])
        s.map('TNotebook.Tab',
              background=[('selected', C['card'])],
              foreground=[('selected', C['primary'])])

    def _layout(self):
        self.sidebar = tk.Frame(self, bg=C['sidebar'], width=220)
        self.sidebar.pack(side='left', fill='y'); self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg=C['sidebar'])
        logo.pack(fill='x', pady=(22, 18), padx=18)
        tk.Label(logo, text="🚌", font=('Segoe UI Emoji', 22),
                 bg=C['sidebar'], fg='white').pack(side='left')
        tk.Label(logo, text=" UIU Shuttle", font=H2,
                 bg=C['sidebar'], fg='white').pack(side='left')

        self.nav_items = {}
        for key, icon, label in [
            ('dashboard', '📊', 'Dashboard'),
            ('student',   '🎓', 'Student View'),
            ('people',    '👤', 'People'),
            ('routes',    '🛣️', 'Routes'),
            ('stops',     '🚏', 'Stops'),
            ('shuttles',  '🚌', 'Shuttles'),
            ('schedules', '📅', 'Schedules'),
            ('register',  '📝', 'Registrations'),
            ('punch',     '💳', 'Card Punch'),
            ('reports',   '📈', 'Reports'),
            ('feedback',  '⭐', 'Feedback'),
        ]:
            b = tk.Button(self.sidebar, text=f"  {icon}   {label}", font=NAV,
                          bg=C['sidebar'], fg=C['sidebar_text'],
                          activebackground=C['sidebar_hover'], activeforeground='white',
                          relief='flat', bd=0, anchor='w', padx=14, pady=10,
                          cursor='hand2', command=lambda k=key: self._show(k))
            b.pack(fill='x', padx=8, pady=2)
            self.nav_items[key] = b

        tk.Frame(self.sidebar, bg=C['sidebar']).pack(fill='both', expand=True)
        tk.Button(self.sidebar, text="  ⏻   Exit", font=NAV,
                  bg=C['sidebar'], fg=C['sidebar_text'],
                  activebackground=C['danger'], activeforeground='white',
                  relief='flat', bd=0, anchor='w', padx=14, pady=12,
                  cursor='hand2', command=self.destroy).pack(fill='x', side='bottom')

        self.content = tk.Frame(self, bg=C['bg'])
        self.content.pack(side='left', fill='both', expand=True)
        self.frames = {}; self.current = None

    def _show(self, key):
        for k, b in self.nav_items.items():
            b.configure(bg=C['sidebar_act'] if k == key else C['sidebar'],
                        fg='white' if k == key else C['sidebar_text'])
        if self.current and self.current in self.frames:
            self.frames[self.current].pack_forget()
        if key not in self.frames:
            self.frames[key] = FRAME_REGISTRY[key](self.content, self)
        self.frames[key].pack(fill='both', expand=True)
        self.current = key
        try:
            self.frames[key].refresh()
        except Exception as e:
            messagebox.showerror("Refresh error", str(e))


if __name__ == "__main__":
    App().mainloop()