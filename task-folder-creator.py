from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


# ============================================================================
# НАЛАШТУВАННЯ
# ============================================================================

BASE_DIRECTORY = r"./workspace"
TEMPLATE_FILE = r"./template/task.md"


# Заборонені символи для імен файлів/каталогів Windows
INVALID_CHARS_PATTERN = r'[<>:"/\\|?*]'


# ============================================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================================

def sanitize_name(text: str) -> str:
    """
    Замінює заборонені символи на '_'
    та прибирає зайві підкреслення.
    """
    text = re.sub(INVALID_CHARS_PATTERN, "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip(" ._")


def obsidian_datetime() -> str:
    """
    Формат дати для Obsidian.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def build_folder_name(
    selected_date: datetime,
    task_id: str,
    title: str
) -> str:
    """
    Формує ім'я каталогу:
    YYMMDD-ID-Title
    або
    YYMMDD-Title
    """

    date_part = selected_date.strftime("%y%m%d")

    safe_title = sanitize_name(title)
    safe_id = sanitize_name(task_id)

    prefix_parts = [date_part]

    if safe_id:
        prefix_parts.append(safe_id)

    prefix = "-".join(prefix_parts)

    # Загальна довжина каталогу не більше 230 символів
    max_folder_length = 230

    reserved_length = len(prefix) + 1  # символ '-'
    max_title_length = max_folder_length - reserved_length

    if max_title_length < 1:
        raise ValueError(
            "Занадто довгий ідентифікатор заявки."
        )

    safe_title = safe_title[:max_title_length]

    return f"{prefix}-{safe_title}"


def create_note_file(
    folder_path: Path,
    title: str,
    task_id: str
) -> None:
    """
    Створює markdown-файл на основі шаблону.
    """

    template_path = Path(TEMPLATE_FILE)

    if not template_path.exists():
        raise FileNotFoundError(
            f"Не знайдено шаблон:\n{template_path}"
        )

    content = template_path.read_text(
        encoding="utf-8"
    )

    now_value = obsidian_datetime()

    replacements = {
        "{{ title }}": title,
        "{{ task_id }}": task_id,
        "{{ created_at }}": now_value,
        "{{ updated_at }}": now_value,
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    note_name = sanitize_name(title)

    if not note_name:
        note_name = "Note"

    note_file = folder_path / f"{note_name}.md"

    note_file.write_text(
        content,
        encoding="utf-8"
    )


# ============================================================================
# GUI
# ============================================================================

class CreateTaskDialog:

    def __init__(self, root: tk.Tk):
        self.root = root

        self.root.title("Створення заявки")
        self.root.resizable(False, False)

        self.create_widgets()

        self.root.bind("<Escape>", lambda e: self.cancel())
        self.root.bind("<Return>", lambda e: self.create())

    def create_widgets(self):
        padding = {"padx": 8, "pady": 4}

        tk.Label(
            self.root,
            text="Дата (YYYY-MM-DD)*"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            **padding
        )

        self.date_var = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )

        tk.Entry(
            self.root,
            textvariable=self.date_var,
            width=40
        ).grid(
            row=0,
            column=1,
            **padding
        )

        tk.Label(
            self.root,
            text="ID заявки"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            **padding
        )

        self.id_var = tk.StringVar()

        tk.Entry(
            self.root,
            textvariable=self.id_var,
            width=40
        ).grid(
            row=1,
            column=1,
            **padding
        )

        tk.Label(
            self.root,
            text="Заголовок*"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            **padding
        )

        self.title_var = tk.StringVar()

        title_entry = tk.Entry(
            self.root,
            textvariable=self.title_var,
            width=40
        )

        title_entry.grid(
            row=2,
            column=1,
            **padding
        )

        title_entry.focus_set()

        button_frame = tk.Frame(self.root)
        button_frame.grid(
            row=3,
            column=0,
            columnspan=2,
            pady=10
        )

        tk.Button(
            button_frame,
            text="Створити",
            width=15,
            command=self.create
        ).pack(
            side=tk.LEFT,
            padx=5
        )

        tk.Button(
            button_frame,
            text="Відмінити",
            width=15,
            command=self.cancel
        ).pack(
            side=tk.LEFT,
            padx=5
        )

    def cancel(self):
        self.root.destroy()

    def create(self):
        try:
            date_text = self.date_var.get().strip()
            task_id = self.id_var.get().strip()
            title = self.title_var.get().strip()

            if not date_text:
                raise ValueError(
                    "Поле дати є обов'язковим."
                )

            if not title:
                raise ValueError(
                    "Поле заголовка є обов'язковим."
                )

            selected_date = datetime.strptime(
                date_text,
                "%Y-%m-%d"
            )

            folder_name = build_folder_name(
                selected_date=selected_date,
                task_id=task_id,
                title=title
            )

            base_path = Path(BASE_DIRECTORY)

            if not base_path.exists():
                raise FileNotFoundError(
                    f"Не знайдено каталог:\n{base_path}"
                )

            folder_path = base_path / folder_name

            folder_path.mkdir(
                parents=False,
                exist_ok=False
            )

            create_note_file(
                folder_path=folder_path,
                title=title,
                task_id=task_id
            )

            messagebox.showinfo(
                "Готово",
                "Каталог і нотатку успішно створено."
            )

            self.root.destroy()

        except Exception as exc:
            messagebox.showerror(
                "Помилка",
                str(exc)
            )


# ============================================================================
# ЗАПУСК
# ============================================================================

def main():
    root = tk.Tk()

    dialog = CreateTaskDialog(root)

    root.mainloop()


if __name__ == "__main__":
    main()