# main.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os

from parser import parse_log
from model import Node

TYPE_COLORS = {
    "event": "#FFD700",  # жовтий, добре читається
    "class": "#4EC9B0",
    "method": "#DCDCAA",
    "function": "#C586C0",
    "int": "#B5CEA8",
    "float": "#B5CEA8",
    "bool": "#569CD6",
    "str": "#CE9178",
    "dict": "#9CDCFE",
    "list": "#9CDCFE",
    "tuple": "#9CDCFE",
    "other": "#d4d4d4",
}

FILTER_TYPES = [
    "event",
    "class", "method", "function",
    "int", "float", "bool", "str",
    "dict", "list", "tuple", "other"
]

data = None
current_log_path = None
item_to_node = {}
right_clicked_item = None


def open_log_file():
    global data, current_log_path

    path = filedialog.askopenfilename(
        title="Open log file",
        filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")]
    )

    if not path:
        return

    try:
        data, root_name = parse_log(path)
        current_log_path = path
        rebuild_tree()
        if root_name:
            root.title(f"WoT Object Browser — {root_name}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    if path in recent_files:
        recent_files.remove(path)

    recent_files.insert(0, path)
    recent_files[:] = recent_files[:10]  # максимум 10


def build_treeview(treeview, parent_id, node):
    for child in node.children:
        tag = child.short_type() or "other"

        item_id = treeview.insert(
            parent_id,
            "end",
            text=child.name,
            values=(child.type,),
            tags=(tag,)
        )

        item_to_node[item_id] = child

        build_treeview(treeview, item_id, child)



# Функція перебудови дерева по фільтру
def rebuild_tree():
    tree.delete(*tree.get_children())
    item_to_node.clear()

    if not data:
        return

    allowed = {t for t, v in filter_vars.items() if v.get()}

    filtered = data.filter(allowed)

    if not filtered:
        return

    search_text = search_var.get().strip()

    if search_text:
        # фільтруємо ТІЛЬКИ дітей ROOT
        new_root = Node("ROOT", None, -1)
        for child in filtered.children:
            f = child.filter_by_name(search_text)
            if f:
                new_root.children.append(f)
        filtered = new_root

    if filtered:
        build_treeview(tree, "", filtered)
    # Кількість вузлів
    count = count_tree_items()
    status_var.set(f"Об'єктів: {count}")


# Функції розкривання
def expand_all(item=""):
    for child in tree.get_children(item):
        tree.item(child, open=True)
        expand_all(child)
# Функції закривання
def collapse_all(item=""):
    for child in tree.get_children(item):
        tree.item(child, open=False)
        collapse_all(child)

# Поставити галочки
def select_all_types():
    for var in filter_vars.values():
        var.set(True)
    rebuild_tree()
# Зняти галочки
def clear_all_types():
    for var in filter_vars.values():
        var.set(False)
    rebuild_tree()

# Витягаємо повний шлях об'єкта
def get_full_path(item_id):
    parts = []

    while item_id:
        node = item_to_node.get(item_id)
        if node:
            parts.append(node.name)
        item_id = tree.parent(item_id)

    return ".".join(reversed(parts))

# Клік по об'єкту
def on_item_click(event):
    item_id = tree.focus()
    if not item_id:
        return

    path = get_full_path(item_id)

    root.clipboard_clear()
    root.clipboard_append(path)

# Копіювання шляху
def copy_selected_path():
    if not right_clicked_item:
        return

    path = get_full_path(right_clicked_item)

    root.clipboard_clear()
    root.clipboard_append(path)
# Копіювання імені
def copy_selected_name():
    if not right_clicked_item:
        return

    node = item_to_node.get(right_clicked_item)
    if not node:
        return

    root.clipboard_clear()
    root.clipboard_append(node.name)
# Копіювання типу
def copy_selected_type():
    if not right_clicked_item:
        return

    node = item_to_node.get(right_clicked_item)
    if not node:
        return

    root.clipboard_clear()
    root.clipboard_append(node.type)

# Клік ПКМ
def on_right_click(event):
    global right_clicked_item

    item_id = tree.identify_row(event.y)
    if not item_id:
        return

    right_clicked_item = item_id
    tree.selection_set(item_id)
    tree.focus(item_id)
    context_menu.tk_popup(event.x_root, event.y_root)

# Підрахунок вузлів дерева
def count_tree_items(item=""):
    count = 0
    for child in tree.get_children(item):
        count += 1
        count += count_tree_items(child)
    return count
# Меню Недавні файли
def show_recent_menu(widget):
    recent_menu.delete(0, "end")

    if not recent_files:
        recent_menu.add_command(label="(Порожньо)", state="disabled")
    else:
        for path in recent_files:
            recent_menu.add_command(
                label=path,
                command=lambda p=path: open_recent_file(p)
            )

    x = widget.winfo_rootx()
    y = widget.winfo_rooty() + widget.winfo_height()
    recent_menu.tk_popup(x, y)
# Відкриття недавного файлу
def open_recent_file(path):
    global data, current_log_path

    if not os.path.exists(path):
        messagebox.showerror("Error", "File not found")
        recent_files.remove(path)
        return

    data, root_name = parse_log(path)
    current_log_path = path
    rebuild_tree()
    root.title(f"WoT Object Browser — {root_name}")


root = tk.Tk()
# Шрифт кнопок, чекбоксів, позначок
import tkinter.font as tkfont
default_font = tkfont.nametofont("TkDefaultFont")
default_font.configure(size=10)

# Статус бар
status_var = tk.StringVar(value="Objects: 0")
# Основне вікно
main_frame = tk.Frame(root, bg="#1e1e1e")
main_frame.pack(fill="both", expand=True)

# Статус бар
status_bar = tk.Label(
    root,
    textvariable=status_var,
    bg="#252526",
    fg="#d4d4d4",
    anchor="w",
    padx=8
)
status_bar.pack(side="bottom", fill="x")
status_bar.config(font=("Segoe UI", 10))


# Ліва панель
left_panel = tk.Frame(main_frame, bg="#1e1e1e", width=180)

# Кнопка відкриття log-файлу
open_frame = tk.Frame(left_panel, bg="#1e1e1e")
open_frame.pack(fill="x", padx=6, pady=(6, 6))
# Основна кнопка
btn_open = tk.Button(
    open_frame,
    text="Відкрити log файл",
    command=open_log_file,
    bg="#0E639C",
    fg="#ffffff",
    relief="flat"
)
btn_open.pack(side="left", fill="x", expand=True)
# Кнопка недавніх файлів
btn_recent = tk.Button(
    open_frame,
    text="▼",
    width=2,
    bg="#0E639C",
    fg="#ffffff",
    relief="flat",
    command=lambda: show_recent_menu(btn_recent)
)
btn_recent.pack(side="right")

recent_menu = tk.Menu(root, tearoff=0)
recent_files = []


# Кнопка розкривання
btn_expand = tk.Button(
    left_panel,
    text="Розгорнути все",
    command=expand_all,
    bg="#252526",
    fg="#d4d4d4",
    relief="flat"
)
btn_expand.pack(fill="x", padx=6, pady=(6, 2))
# Кнопка закривання
btn_collapse = tk.Button(
    left_panel,
    text="Згорнути все",
    command=collapse_all,
    bg="#252526",
    fg="#d4d4d4",
    relief="flat"
)
btn_collapse.pack(fill="x", padx=6, pady=(0, 6))


# Вибрати чекбокси
btn_select_all = tk.Button(
    left_panel,
    text="Вибрати всі",
    command=select_all_types,
    bg="#252526",
    fg="#d4d4d4",
    relief="flat"
)
btn_select_all.pack(fill="x", padx=6, pady=(6, 2))
# Зняти чекбокси
btn_clear_all = tk.Button(
    left_panel,
    text="Очистити всі",
    command=clear_all_types,
    bg="#252526",
    fg="#d4d4d4",
    relief="flat"
)
btn_clear_all.pack(fill="x", padx=6, pady=(0, 6))


# Пошук
tk.Label(
    left_panel,
    text="Пошук",
    bg="#1e1e1e",
    fg="#d4d4d4"
).pack(anchor="w", padx=6)

search_var = tk.StringVar()
search_entry = tk.Entry(
    left_panel,
    textvariable=search_var,
    bg="#252526",
    fg="#d4d4d4",
    insertbackground="#ffffff",
    relief="flat"
)
search_entry.pack(fill="x", padx=6, pady=(0, 6))

search_var.trace_add("write", lambda *_: rebuild_tree())

left_panel.pack(side="left", fill="y")


# Права панель
right_panel = tk.Frame(main_frame, bg="#1e1e1e")
right_panel.pack(side="right", fill="both", expand=True)

root.title("WoT Object Browser")
root.geometry("1100x800")
root.minsize(750, 650)


style = ttk.Style()
style.theme_use("default")

style.configure(
    "Vertical.TScrollbar",
    background="#2a2a2a",
    troughcolor="#1e1e1e",
    bordercolor="#1e1e1e",
    arrowcolor="#d4d4d4",
    lightcolor="#2a2a2a",
    darkcolor="#2a2a2a",
    focuscolor="#1e1e1e"
)
style.map(
    "Vertical.TScrollbar",
    background=[("disabled", "#2a2a2a")],
    troughcolor=[("disabled", "#1e1e1e")],
    arrowcolor=[("disabled", "#555555")]
)


style.configure(
    "Treeview",
    background="#1e1e1e",
    foreground="#d4d4d4",
    fieldbackground="#1e1e1e",
    rowheight=23,
    font=("Segoe UI", 12),
)
style.map(
    "Treeview",
    background=[("selected", "#264F78")],
    foreground=[("selected", "#ffffff")]
)

style.configure(
    "Treeview.Heading",
    background="#252526",
    foreground="#d4d4d4",
    relief="flat",
    font=("Segoe UI", 12),
)
style.map(
    "Treeview.Heading",
    background=[("active", "#333333")]
)


tree_frame = tk.Frame(right_panel, bg="#1e1e1e")
tree_frame.pack(fill="both", expand=True)

scrollbar = ttk.Scrollbar(
    tree_frame,
    orient="vertical",
    style="Vertical.TScrollbar"
)


tree = ttk.Treeview(
    tree_frame,
    columns=("type",),
    yscrollcommand=scrollbar.set,
    show="tree headings"
)

scrollbar.config(command=tree.yview)

# Розміри колонок
tree.heading("#0", text="Name")
tree.heading("type", text="Type")
tree.column("#0", width=250, minwidth=200, stretch=True)
tree.column("type", width=350, minwidth=250, stretch=True)
tree.bind("<Button-3>", on_right_click)

tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# Меню на ПКМ
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(
    label="Копіювати шлях",
    command=lambda: copy_selected_path()
)

context_menu.add_command(
    label="Копіювати ім'я",
    command=lambda: copy_selected_name()
)

context_menu.add_command(
    label="Копіювати тип",
    command=lambda: copy_selected_type()
)



# Змінні чекбоксів
filter_vars = {}

for t in FILTER_TYPES:
    var = tk.BooleanVar(value=True)
    cb = tk.Checkbutton(
        left_panel,
        text=t,
        variable=var,
        bg="#1e1e1e",
        fg=TYPE_COLORS.get(t, "#d4d4d4"),
        selectcolor="#1e1e1e",
        activebackground="#1e1e1e",
        activeforeground="#ffffff"
    )
    cb.pack(anchor="w", padx=8, pady=2)
    filter_vars[t] = var
    cb.config(command=rebuild_tree)

for tag, color in TYPE_COLORS.items():
    tree.tag_configure(tag, foreground=color)


data, root_name = parse_log("test.log")

if root_name:
    root.title(f"WoT Object Browser — {root_name}")

rebuild_tree()


root.mainloop()
