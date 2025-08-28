# file: admin_app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os

class ProductAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Менеджер товарів")
        self.root.geometry("1000x650")

        # ===== Поле для API URL =====
        tk.Label(root, text="Адреса API:").pack(pady=5)
        self.api_url_var = tk.StringVar(value="http://127.0.0.1:8000")
        tk.Entry(root, textvariable=self.api_url_var, width=50).pack(pady=5)
        tk.Button(root, text="Підключитися", command=self.refresh_products).pack(pady=5)

        # ===== Кнопка Додати товар =====
        add_btn = tk.Button(root, text="Додати товар", command=self.add_product_window)
        add_btn.pack(pady=10)

        # ===== Статус сервера =====
        self.status_label = tk.Label(root, text="Server status: ...")
        self.status_label.pack(pady=10)

        # ===== Таблиця продуктів =====
        self.tree = ttk.Treeview(root, columns=("name", "price", "image"), show="headings", height=20)
        self.tree.heading("name", text="Назва")
        self.tree.heading("price", text="Ціна/кг")
        self.tree.heading("image", text="Фото")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-3>", self.right_click_menu)

        # Контекстне меню ПКМ
        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="Редагувати", command=self.edit_selected)
        self.menu.add_command(label="Видалити", command=self.delete_selected)

        self.products = []

        # ===== Перше завантаження і автоперезавантаження =====
        self.refresh_products_periodically()

    # ===== ПКМ меню =====
    def right_click_menu(self, event):
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            self.tree.selection_set(selected_item)
            self.menu.post(event.x_root, event.y_root)

    # ===== Отримати продукти =====
    def refresh_products(self):
        api_url = self.api_url_var.get()
        try:
            response = requests.get(f"{api_url}/products")
            self.products = response.json()
            self.tree.delete(*self.tree.get_children())
            for p in self.products:
                self.tree.insert("", "end", iid=p["id"], values=(
                    p["name"],
                    p["price_per_kg"],
                    os.path.basename(p["image_path"])
                ))
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити товари:\n{e}")

    # ===== Оновити статус сервера =====
    def refresh_status(self):
        api_url = self.api_url_var.get()
        try:
            response = requests.get(f"{api_url}/status")
            try:
                status_json = response.json()
                status_text = status_json.get("status", "unknown")
            except:
                status_text = response.text
            self.status_label.config(text=f"Server status: {status_text}")
        except Exception as e:
            self.status_label.config(text=f"Server status: Error ({e})")

    # ===== Періодичне оновлення таблиці та статусу =====
    def refresh_products_periodically(self):
        self.refresh_products()
        self.root.after(5000, self.refresh_products_periodically)  # кожні 5 секунд

    # ===== Модальне вікно додавання =====
    def add_product_window(self):
        win = tk.Toplevel(self.root)
        win.title("Додати товар")
        win.geometry("400x300")

        tk.Label(win, text="Назва:").pack()
        name_entry = tk.Entry(win)
        name_entry.pack()

        tk.Label(win, text="Ціна за кг:").pack()
        price_entry = tk.Entry(win)
        price_entry.pack()

        tk.Label(win, text="Фото:").pack()
        photo_path = tk.StringVar()
        tk.Entry(win, textvariable=photo_path).pack()
        def browse_file():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if path:
                photo_path.set(path)
        tk.Button(win, text="Вибрати файл", command=browse_file).pack(pady=5)

        def submit():
            if not name_entry.get() or not price_entry.get() or not photo_path.get():
                messagebox.showwarning("Помилка", "Заповніть усі поля")
                return
            api_url = self.api_url_var.get()
            try:
                with open(photo_path.get(), "rb") as f:
                    files = {"image": f}
                    data = {"name": name_entry.get(), "price_per_kg": float(price_entry.get())}
                    requests.post(f"{api_url}/products", data=data, files=files)
                win.destroy()
                self.refresh_products()
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося додати товар:\n{e}")

        tk.Button(win, text="Додати", command=submit).pack(pady=10)

    # ===== Редагування =====
    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        product_id = selected[0]
        product = next((p for p in self.products if p["id"] == product_id), None)
        if not product:
            return

        win = tk.Toplevel(self.root)
        win.title("Редагувати товар")
        win.geometry("400x300")

        tk.Label(win, text="Назва:").pack()
        name_entry = tk.Entry(win)
        name_entry.insert(0, product["name"])
        name_entry.pack()

        tk.Label(win, text="Ціна за кг:").pack()
        price_entry = tk.Entry(win)
        price_entry.insert(0, str(product["price_per_kg"]))
        price_entry.pack()

        tk.Label(win, text="Фото:").pack()
        photo_path = tk.StringVar()
        tk.Entry(win, textvariable=photo_path).pack()
        def browse_file():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if path:
                photo_path.set(path)
        tk.Button(win, text="Вибрати файл", command=browse_file).pack(pady=5)

        def submit():
            api_url = self.api_url_var.get()
            try:
                data = {"name": name_entry.get(), "price_per_kg": float(price_entry.get())}
                if photo_path.get():
                    with open(photo_path.get(), "rb") as f:
                        files = {"image": f}
                        requests.put(f"{api_url}/products/{product_id}", data=data, files=files)
                else:
                    requests.put(f"{api_url}/products/{product_id}", data=data)
                win.destroy()
                self.refresh_products()
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося редагувати товар:\n{e}")

        tk.Button(win, text="Зберегти", command=submit).pack(pady=10)

    # ===== Видалення =====
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        product_id = selected[0]
        if messagebox.askyesno("Видалити?", "Видалити цей товар?"):
            api_url = self.api_url_var.get()
            try:
                requests.delete(f"{api_url}/products/{product_id}")
                self.refresh_products()
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося видалити товар:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductAdminApp(root)
    root.mainloop()
