"""
Inventory & Point-of-Sale (POS) system — Tkinter desktop app.

Features:
  * Login screen
  * Stock list with live search (by product ID or name)
  * Shopping cart with running total
  * "Sale" checks stock, lowers quantities, records profit in sales history
  * Sales history window with a profit pie chart (matplotlib)
  * Settings window to add / edit / delete stock items

Data is stored in two JSON files next to this script:
  stock.json          -> [product_id, name, cost_price, quantity, selling_price, sale_tax_percent]
  sales_history.json  -> [product_id, name, cost_price, selling_price, sale_tax_percent, profit]
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_FILE = os.path.join(BASE_DIR, "stock.json")
HISTORY_FILE = os.path.join(BASE_DIR, "sales_history.json")

# Demo credentials — change these before using the app for anything real.
USERNAME = "admin"
PASSWORD = "admin"

# Column indexes in a stock item
ID, NAME, COST, QTY, PRICE, TAX = range(6)

stock = []          # list of stock items
cart_list = []      # [id, name, cost, selling price, tax]
sales_history = []  # [id, name, cost, selling price, tax, profit]


# data / logic

def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data():
    stock[:] = _load(STOCK_FILE)
    sales_history[:] = _load(HISTORY_FILE)


def save_data():
    with open(STOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=2)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sales_history, f, indent=2)


def find_stock_item(product_id):
    for item in stock:
        if item[ID] == product_id:
            return item
    return None


def calculate_profit(cost_price, selling_price, sale_tax):
    """Profit = selling price - cost price - tax (tax is a % of selling price)."""
    return round((selling_price - cost_price) - (sale_tax * selling_price / 100), 2)


def process_sale():
    """Sell everything in the cart. Returns (ok, message)."""
    if not cart_list:
        return False, "The cart is empty."

    # Check stock for the whole cart first, so a failed sale changes nothing.
    needed = {}
    for item in cart_list:
        needed[item[0]] = needed.get(item[0], 0) + 1
    for product_id, qty in needed.items():
        stock_item = find_stock_item(product_id)
        if stock_item is None or stock_item[QTY] < qty:
            name = stock_item[NAME] if stock_item else product_id
            return False, f"Not enough quantity in stock for {name}."

    for product_id, qty in needed.items():
        find_stock_item(product_id)[QTY] -= qty

    for item in cart_list:
        profit = calculate_profit(item[2], item[3], item[4])
        sales_history.append(item[:5] + [profit])

    cart_list.clear()
    save_data()
    return True, "Sale completed."


def out_of_stock_names():
    return [item[NAME] for item in stock if item[QTY] == 0]


#  UI helpers

def make_tree(parent, columns):
    tree = ttk.Treeview(parent, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack(pady=10)
    return tree


def fill_stock_tree(tree, data):
    tree.delete(*tree.get_children())
    for item in data:
        tree.insert("", "end", values=(item[ID], item[NAME], item[QTY], item[PRICE]))


def item_form(parent, title, values=None, on_save=None, lock_id=False):
    """Shared Add/Edit form. Calls on_save(new_item) with parsed values."""
    window = tk.Toplevel(parent)
    window.title(title)
    labels = ["Product ID", "Name", "Cost Price", "Quantity", "Selling Price", "Sale Tax (%)"]
    entries = []
    for row, label in enumerate(labels):
        tk.Label(window, text=label + ":").grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
        entry = tk.Entry(window)
        entry.grid(row=row, column=1, padx=10, pady=5)
        if values is not None:
            entry.insert(0, values[row])
        entries.append(entry)
    if lock_id:
        entries[0].config(state="disabled")

    def save():
        try:
            new_item = [
                entries[0].get().strip(),
                entries[1].get().strip(),
                float(entries[2].get()),
                int(entries[3].get()),
                float(entries[4].get()),
                float(entries[5].get()),
            ]
        except ValueError:
            messagebox.showerror("Invalid input", "Prices and tax must be numbers, quantity a whole number.",
                                 parent=window)
            return
        if not new_item[0] or not new_item[1]:
            messagebox.showerror("Invalid input", "Product ID and name are required.", parent=window)
            return
        if on_save(new_item, window):
            window.destroy()

    tk.Button(window, text="Save", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)


# main window

def open_main_page():
    main = tk.Tk()
    main.title("Inventory & POS")

    tk.Label(main, text="Company Name", font=("Helvetica", 16, "bold")).pack(pady=10)

    stock_tree = make_tree(main, ("Product ID", "Name", "Quantity", "Selling Price"))

    search_var = tk.StringVar()
    search_entry = tk.Entry(main, textvariable=search_var, width=30)
    search_entry.pack(pady=5)

    def refresh_stock():
        query = search_var.get().lower()
        results = [i for i in stock if query in str(i[ID]).lower() or query in i[NAME].lower()]
        fill_stock_tree(stock_tree, results)

    search_entry.bind("<KeyRelease>", lambda event: refresh_stock())

    total_label = tk.Label(main, text="Total Price: $0.00", font=("Helvetica", 14, "bold"))

    def refresh_cart():
        cart_tree.delete(*cart_tree.get_children())
        for item in cart_list:
            cart_tree.insert("", "end", values=(item[0], item[1], item[3]))
        total = sum(item[3] for item in cart_list)
        total_label.config(text=f"Total Price: ${total:.2f}")

    def add_to_cart():
        values = stock_tree.item(stock_tree.focus(), "values")
        if not values:
            messagebox.showwarning("No Item Selected", "Select an item from the stock to add to the cart.")
            return
        item = find_stock_item(values[0])
        cart_list.append([item[ID], item[NAME], item[COST], item[PRICE], item[TAX]])
        refresh_cart()

    def remove_from_cart():
        values = cart_tree.item(cart_tree.focus(), "values")
        if not values:
            messagebox.showwarning("No Item Selected", "Select an item from the cart to remove.")
            return
        for item in cart_list:
            if item[0] == values[0]:
                cart_list.remove(item)
                break
        refresh_cart()

    def sale():
        if not messagebox.askyesno("Confirmation", "Are you sure you want to proceed with the sale?"):
            messagebox.showinfo("Sale Canceled", "Sale has been canceled.")
            return
        ok, msg = process_sale()
        (messagebox.showinfo if ok else messagebox.showwarning)("Sale", msg)
        refresh_cart()
        refresh_stock()
        empty = out_of_stock_names()
        if ok and empty:
            messagebox.showinfo("Zero Quantity Items",
                                "The following items have reached zero quantity:\n" + ", ".join(empty))

    def history_page():
        window = tk.Toplevel(main)
        window.title("Sales History")
        tree = make_tree(window, ("Product ID", "Name", "Cost Price", "Selling Price", "Sale Tax", "Profit"))
        for item in sales_history:
            tree.insert("", "end", values=tuple(item[:6]))

        def clear_history():
            if messagebox.askyesno("Clear History", "Delete all sales history?", parent=window):
                sales_history.clear()
                save_data()
                window.destroy()

        def show_pie_chart():
            # Group profit by product; a pie chart can't show negative slices.
            totals = {}
            for item in sales_history:
                totals[item[1]] = totals.get(item[1], 0) + item[5]
            totals = {name: p for name, p in totals.items() if p > 0}
            if not totals:
                messagebox.showinfo("No data", "No profitable sales to chart yet.", parent=window)
                return
            plt.figure()
            plt.pie(list(totals.values()), labels=list(totals.keys()), autopct="%1.1f%%", startangle=140)
            plt.title("Profit Distribution")
            plt.show()

        tk.Button(window, text="Clear History", command=clear_history).pack(pady=5)
        tk.Button(window, text="Show Pie Chart", command=show_pie_chart).pack(pady=5)

    def settings_page():
        window = tk.Toplevel(main)
        window.title("Settings")
        tree = make_tree(window, ("Product ID", "Name", "Quantity", "Selling Price"))

        def refresh_all():
            fill_stock_tree(tree, stock)
            refresh_stock()

        def add_item():
            def on_save(new_item, form):
                if find_stock_item(new_item[ID]):
                    messagebox.showerror("Duplicate ID", "A product with this ID already exists.", parent=form)
                    return False
                stock.append(new_item)
                save_data()
                refresh_all()
                return True
            item_form(window, "Add Item to Stock", on_save=on_save)

        def edit_item():
            values = tree.item(tree.focus(), "values")
            if not values:
                messagebox.showwarning("No Item Selected", "Select an item to edit.", parent=window)
                return
            existing = find_stock_item(values[0])

            def on_save(new_item, form):
                new_item[ID] = existing[ID]  # ID field is locked
                existing[:] = new_item
                save_data()
                refresh_all()
                return True
            item_form(window, "Edit Item", values=existing, on_save=on_save, lock_id=True)

        def delete_item():
            values = tree.item(tree.focus(), "values")
            if not values:
                messagebox.showwarning("No Item Selected", "Select an item to delete.", parent=window)
                return
            if messagebox.askyesno("Confirm Deletion", "Delete the selected item?", parent=window):
                stock.remove(find_stock_item(values[0]))
                save_data()
                refresh_all()

        tk.Button(window, text="Add Item", command=add_item).pack(pady=5)
        tk.Button(window, text="Edit Item", command=edit_item).pack(pady=5)
        tk.Button(window, text="Delete Item", command=delete_item).pack(pady=5)
        fill_stock_tree(tree, stock)

    tk.Button(main, text="Add to Cart", command=add_to_cart).pack(pady=5)
    tk.Button(main, text="Remove from Cart", command=remove_from_cart).pack(pady=5)
    total_label.pack(pady=10)
    cart_tree = make_tree(main, ("Product ID", "Name", "Selling Price"))
    tk.Button(main, text="Sale", command=sale).pack(pady=5)
    tk.Button(main, text="History", command=history_page).pack(pady=5, side="left")
    tk.Button(main, text="Settings", command=settings_page).pack(pady=5, side="left")

    refresh_stock()
    main.mainloop()


# login window

def login_page():
    """Returns True if the user logged in successfully."""
    result = {"ok": False}
    root = tk.Tk()
    root.title("Login Page")

    tk.Label(root, text="Username:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
    username_entry = tk.Entry(root)
    username_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(root, text="Password:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
    password_entry = tk.Entry(root, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    def validate_login(event=None):
        if username_entry.get() == USERNAME and password_entry.get() == PASSWORD:
            result["ok"] = True
            root.destroy()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password!")

    tk.Button(root, text="Login", command=validate_login).grid(row=2, column=0, columnspan=2, pady=10)
    root.bind("<Return>", validate_login)
    username_entry.focus()
    root.mainloop()
    return result["ok"]


if __name__ == "__main__":
    load_data()
    if login_page():
        open_main_page()
