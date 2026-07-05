import sqlite3 as sq
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import csv

conn = sq.connect('store.sqlite')
crs = conn.cursor()

crs.execute('''
CREATE TABLE IF NOT EXISTS customer(
    id INTEGER PRIMARY KEY,
    name TEXT,
    surname VARCHAR
)
''')

crs.execute('''
CREATE TABLE IF NOT EXISTS invoice(
    id INTEGER PRIMARY KEY,
    product TEXT,
    price INTEGER
)
''')

crs.execute('''
CREATE TABLE IF NOT EXISTS storage(
    id INTEGER PRIMARY KEY,
    product TEXT,
    count VARCHAR
)
''')
conn.commit()

class StoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title(wn_title)
        self.root.geometry(wn_size)
 
        btn_customer = tk.Button(root, text="Customers", width=20, command=self.open_customer_window,bg='#4a90e2')
        btn_customer.pack(pady=10)

        btn_invoice = tk.Button(root, text="Invoices", width=20, command=self.open_invoice_window,bg='#50c878')
        btn_invoice.pack(pady=10)

        btn_storage = tk.Button(root, text="Storage", width=20, command=self.open_storage_window,bg='#ffb347')
        btn_storage.pack(pady=10)

        btn_export = tk.Button(root, text="Export CSV", width=20, command=self.export_csv,bg='#9b59b6')
        btn_export.pack(pady=10)

    def open_customer_window(self):
        window = tk.Toplevel(self.root)
        window.title("Customers")
        window.geometry("600x400")

        tree = ttk.Treeview(window, columns=("ID", "Name", "Surname"), show='headings')
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Surname", text="Surname")
        tree.pack(expand=True, fill='both')

        def load_data():
            for i in tree.get_children():
                tree.delete(i)
            crs.execute("SELECT * FROM customer")
            for row in crs.fetchall():
                tree.insert('', 'end', values=row)

        load_data()

        def add_customer():
            name = simpledialog.askstring("Input", "Enter name:", parent=window)
            if not name:
                return
            surname = simpledialog.askstring("Input", "Enter surname:", parent=window)
            if not surname:
                return
            crs.execute("INSERT INTO customer (name,surname) VALUES (?,?)", (name,surname))
            conn.commit()
            load_data()

        def delete_customer():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select a customer to delete")
                return
            item = tree.item(selected[0])
            cid = item['values'][0]
            if messagebox.askyesno("Confirm", "Are you sure to delete this customer?"):
                crs.execute("DELETE FROM customer WHERE id=?", (cid,))
                conn.commit()
                load_data()

        def update_customer():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select a customer to update")
                return
            item = tree.item(selected[0])
            cid, name_old, surname_old = item['values']

            name = simpledialog.askstring("Input", "Enter new name:", initialvalue=name_old, parent=window)
            if not name:
                return
            surname = simpledialog.askstring("Input", "Enter new surname:", initialvalue=surname_old, parent=window)
            if not surname:
                return
            crs.execute("UPDATE customer SET name=?, surname=? WHERE id=?", (name, surname, cid))
            conn.commit()
            load_data()

        frame_buttons = tk.Frame(window)
        frame_buttons.pack(pady=10)

        tk.Button(frame_buttons, text="Add customer", command=add_customer, bg="#2ecc71").pack(side='left', padx=5)
        tk.Button(frame_buttons, text="Update customer", command=update_customer, bg="#3498db").pack(side='left', padx=5)
        tk.Button(frame_buttons, text="Delete customer", command=delete_customer, bg="#e74c3c").pack(side='left', padx=5)

    def open_invoice_window(self):
        window = tk.Toplevel(self.root)
        window.title("Invoices")
        window.geometry("600x400")

        tree = ttk.Treeview(window, columns=("ID", "Product", "Price"), show='headings')
        tree.heading("ID", text="ID")
        tree.heading("Product", text="Product")
        tree.heading("Price", text="Price")
        tree.pack(expand=True,fill='both')

        def load_data():
            for i in tree.get_children():
                tree.delete(i)
            crs.execute("SELECT * FROM invoice")
            z = crs.fetchall()
            for row in z:
                tree.insert('', 'end', values=row)

        load_data()

        def add_invoice():
            product = simpledialog.askstring("Input", "Enter product:", parent=window)
            if not product:
                return
            price_str = simpledialog.askstring("Input", "Enter price:", parent=window)
            if not price_str or not price_str.isdigit():
                messagebox.showerror("Error", "Price must be a number")
                return
            price = int(price_str)
            crs.execute("INSERT INTO invoice (product, price) VALUES (?, ?)", (product, price))
            conn.commit()
            load_data()

        def delete_invoice():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select an invoice to delete")
                return
            item = tree.item(selected[0])
            iid = item['values'][0]
            if messagebox.askyesno("Confirm", "Are you sure to delete this invoice?"):
                crs.execute("DELETE FROM invoice WHERE id=?", (iid,))
                conn.commit()
                load_data()

        def update_invoice():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select an invoice to update")
                return
            item = tree.item(selected[0])
            iid, product_old, price_old = item['values']

            product = simpledialog.askstring("Input", "Enter new product:", initialvalue=product_old, parent=window)
            if not product:
                return
            price_str = simpledialog.askstring("Input", "Enter new price:", initialvalue=str(price_old), parent=window)
            if not price_str or not price_str.isdigit():
                messagebox.showerror("Error", "Price must be a number")
                return
            price = int(price_str)

            crs.execute("UPDATE invoice SET product=?, price=? WHERE id=?", (product, price, iid))
            conn.commit()
            load_data()

        frame_buttons = tk.Frame(window)
        frame_buttons.pack(pady=10)

        tk.Button(frame_buttons, text="Add invoice", command=add_invoice, bg="#2ecc71").pack(side='left', padx=5)
        tk.Button(frame_buttons, text="Update invoice", command=update_invoice, bg="#3498db").pack(side='left', padx=5)
        tk.Button(frame_buttons, text="Delete invoice", command=delete_invoice, bg="#e74c3c").pack(side='left', padx=5)


    def open_storage_window(self):
        window = tk.Toplevel(self.root)
        window.title("Storage")
        window.geometry("600x400")

        tree = ttk.Treeview(window, columns=("ID", "Product", "Count"), show='headings')
        tree.heading("ID", text="ID")
        tree.heading("Product", text="Product")
        tree.heading("Count", text="Count")
        tree.pack(expand=True,fill='both')

        def load_data():
            for i in tree.get_children():
                tree.delete(i)
            crs.execute("SELECT * FROM storage")
            for row in crs.fetchall():
                tree.insert('', 'end', values=row)

        load_data()

        def add_storage():
            product = simpledialog.askstring("Input", "Enter product:", parent=window)
            if not product:
                return
            count = simpledialog.askstring("Input", "Enter count:", parent=window)
            if not count:
                return
            crs.execute("INSERT INTO storage (product, count) VALUES (?, ?)", (product, count))
            conn.commit()
            load_data()

        def delete_storage():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select a storage item to delete")
                return
            item = tree.item(selected[0])
            sid = item['values'][0]
            if messagebox.askyesno("Confirm", "Are you sure to delete this storage item?"):
                crs.execute("DELETE FROM storage WHERE id=?", (sid,))
                conn.commit()
                load_data()

        def update_storage():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select an item to update")
                return
            item = tree.item(selected[0])
            sid, product_old, count_old = item['values']

            product = simpledialog.askstring("Input", "Enter new product:", initialvalue=product_old, parent=window)
            if not product:
                return
            count = simpledialog.askstring("Input", "Enter new count:", initialvalue=count_old, parent=window)
            if not count:
                return
            crs.execute("UPDATE storage SET product=?, count=? WHERE id=?", (product, count, sid))
            conn.commit()
            load_data()

        frame_buttons = tk.Frame(window)
        frame_buttons.pack(pady=10)

        tk.Button(frame_buttons, text="Add storage", command=add_storage, bg="#2ecc71").pack(side='left', padx=5)
        tk.Button(frame_buttons, text="Update storage", command=update_storage, bg="#3498db").pack(side='left', padx=5)
        tk.Button(frame_buttons, text="Delete storage", command=delete_storage, bg="#e74c3c").pack(side='left', padx=5)

    def export_csv(self):

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save EXEL File"
        )
        

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                writer.writerow(["Customers"])
                crs.execute("SELECT * FROM customer")
                writer.writerow(["ID", "Name", "Surname"])
                for row in crs.fetchall():
                    writer.writerow(row)
                writer.writerow([])  

                writer.writerow(["Invoices"])
                crs.execute("SELECT * FROM invoice")
                writer.writerow(["ID", "Product", "Price"])
                for row in crs.fetchall():
                    writer.writerow(row)
                writer.writerow([])

                writer.writerow(["Storage"])
                crs.execute("SELECT * FROM storage")
                writer.writerow(["ID", "Product", "Count"])
                for row in crs.fetchall(): 
                    writer.writerow(row)

            messagebox.showinfo("Success", f"Data exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{e}")



wn_size = '400x300'
wn_title = 'store Management'
root = tk.Tk()

app = StoreApp(root)

root.mainloop()
conn.close()