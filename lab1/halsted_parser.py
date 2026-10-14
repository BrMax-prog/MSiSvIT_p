import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import math

class HalsteadParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор метрик Холстеда (Scala)")
        self.root.geometry("980x650")

        # Ключевые слова языка Scala (операторы)
        self.keywords = {
            'def', 'var', 'val', 'if', 'while', 'for', 'break', 'continue',
            'return', 'object', 'class', 'new', 'try', 'match'
        }

        # Конструкции, исключаемые из подсчета (например, else считается частью единого if-else)
        self.blacklist = {'else', 'to', 'until', 'case', 'catch', 'finally'}

        # Встроенные типы данных
        self.types = {
            'Int', 'Double', 'String', 'Array', 'Unit',
            'Boolean', 'Long', 'Float', 'Short', 'Byte', 'Char'
        }

        # Встроенные стандартные функции
        self.builtin_funcs = {'println', 'print', 'abs', 'sin', 'cos', 'sqrt'}

        # Настройки классификации
        self.treat_funcs_as_operators = tk.BooleanVar(value=True)
        self.treat_types_as_operators = tk.BooleanVar(value=True)
        # Учитывать скобки () только как оператор группировки в выражениях
        self.only_grouping_parens = tk.BooleanVar(value=True)

        self.setup_ui()

    def setup_ui(self):
        # Левая панель: ввод кода и управление
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="Исходный код (Scala):", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.text_area = tk.Text(left_frame, wrap=tk.NONE, width=45)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Опции анализа
        options_frame = tk.LabelFrame(left_frame, text="Параметры классификации", padx=5, pady=5)
        options_frame.pack(fill=tk.X, pady=5)

        tk.Checkbutton(options_frame, text="Считать функции операторами",
                       variable=self.treat_funcs_as_operators).pack(anchor="w")
        tk.Checkbutton(options_frame, text="Считать типы данных операторами",
                       variable=self.treat_types_as_operators).pack(anchor="w")
        tk.Checkbutton(options_frame, text="Скобки ( ) только в выражениях (группировка)",
                       variable=self.only_grouping_parens).pack(anchor="w")

        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Загрузить файл", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Анализировать", bg="#d1e7dd", command=self.analyze_code).pack(side=tk.RIGHT, padx=5)

        # Правая панель: таблица метрик и результаты
        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="Базовые метрики:", font=("Arial", 10, "bold")).pack(anchor="w")

        columns = ("j", "operator", "f1j", "i", "operand", "f2i")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("j", text="j")
        self.tree.column("j", width=35, anchor="center")
        self.tree.heading("operator", text="Оператор")
        self.tree.column("operator", width=120, anchor="w")
        self.tree.heading("f1j", text="f1j")
        self.tree.column("f1j", width=45, anchor="center")
        
        self.tree.heading("i", text="i")
        self.tree.column("i", width=35, anchor="center")
        self.tree.heading("operand", text="Операнд")
        self.tree.column("operand", width=120, anchor="w")
        self.tree.heading("f2i", text="f2i")
        self.tree.column("f2i", width=45, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.metrics_frame = tk.Frame(right_frame, pady=10)
        self.metrics_frame.pack(fill=tk.X)
        
        self.lbl_dict = tk.Label(self.metrics_frame, text="Словарь программы (η): -", font=("Arial", 10))
        self.lbl_dict.pack(anchor="w")
        
        self.lbl_len = tk.Label(self.metrics_frame, text="Длина программы (N): -", font=("Arial", 10))
        self.lbl_len.pack(anchor="w")
        
        self.lbl_vol = tk.Label(self.metrics_frame, text="Объем программы (V): -", font=("Arial", 10, "bold"))
        self.lbl_vol.pack(anchor="w")

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Scala Files", "*.scala"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                code = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, code)

    def analyze_code(self):
        code = self.text_area.get(1.0, tk.END)
        if not code.strip():
            messagebox.showwarning("Предупреждение", "Введите или загрузите код для анализа.")
            return

        # Находим все объявленные функции заранее: def funcName(...)
        defined_funcs = set(re.findall(r'\bdef\s+([A-Za-z_]\w*)', code))
        all_funcs = defined_funcs | self.builtin_funcs

        operators_count = {}
        operands_count = {}

        # Регулярные выражения для лексера (порядок важен!)
        token_specification = [
            ('COMMENT_SINGLE', r'//[^\n]*'),
            ('COMMENT_MULTI',  r'/\*[\s\S]*?\*/'),
            ('STRING',         r'"(?:\\.|[^"\\])*"'),
            ('FLOAT',          r'\b\d+\.\d+\b'),
            ('INT',            r'\b\d+\b'),
            ('OP_MULTI',       r'<=|>=|==|!=|=>|<-|\+=|-=|\*=|/='),
            ('OP_SINGLE',      r'[+\-*/=<>\:.,()\[\]{}]'),
            ('IDENT',          r'[a-zA-Z_]\w*'),
            ('SKIP',           r'[ \t\r\n]+'),
            ('MISC',           r'.')
        ]
        
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        
        raw_tokens = []
        for mo in re.finditer(tok_regex, code):
            kind = mo.lastgroup
            val = mo.group()
            # Пропускаем комментарии, пробелы и нераспознанные символы
            if kind in ('COMMENT_SINGLE', 'COMMENT_MULTI', 'SKIP', 'MISC'):
                continue
            raw_tokens.append((kind, val))

        # Операторы, предшествующие выражению
        math_prev_ops = {'=', '+', '-', '*', '/', '%', '<', '>', '<=', '>=', '==', '!=', '=>', '<-', '(', ',', 'return'}

        for idx, (kind, val) in enumerate(raw_tokens):
            prev_tok = raw_tokens[idx - 1] if idx > 0 else (None, None)

            # 1. Строковые и числовые литералы -> операнды
            if kind in ('STRING', 'FLOAT', 'INT'):
                operands_count[val] = operands_count.get(val, 0) + 1

            # 2. Составные операторы (<=, >=, ==, != и т.д.)
            elif kind == 'OP_MULTI':
                operators_count[val] = operators_count.get(val, 0) + 1

            # 3. Одиночные символы и скобки
            elif kind == 'OP_SINGLE':
                if val == '{':
                    # Блочный оператор { }
                    operators_count['{ }'] = operators_count.get('{ }', 0) + 1
                elif val == '[':
                    # Индексация типов / массивов [ ]
                    operators_count['[ ]'] = operators_count.get('[ ]', 0) + 1
                elif val == '(':
                    if self.only_grouping_parens.get():
                        # Проверяем, является ли скобка оператором группировки в выражении:
                        # Если перед ней стоит имя функции, переменной, массива или ключевое слово if/while/def/new,
                        # то это синтаксическая скобка вызова/условия/сигнатуры, а НЕ математическая группировка.
                        is_call_or_def = prev_tok[0] == 'IDENT'
                        is_control_or_def = prev_tok[1] in {'if', 'while', 'for', 'def', 'catch', 'new'}
                        is_bracket_call = prev_tok[1] == ']'  # например: Array[Double](size)

                        if not (is_call_or_def or is_control_or_def or is_bracket_call):
                            if prev_tok[1] in math_prev_ops or prev_tok[0] is None:
                                operators_count['( )'] = operators_count.get('( )', 0) + 1
                    else:
                        # Классический подсчёт каждой открывающей скобки как пары ( )
                        operators_count['( )'] = operators_count.get('( )', 0) + 1
                elif val in ('}', ']', ')'):
                    # Закрывающие парные скобки не дублируем
                    continue
                else:
                    # Символы +, -, *, /, =, <, >, :, ., ,
                    operators_count[val] = operators_count.get(val, 0) + 1

            # 4. Идентификаторы, ключевые слова, типы, имена функций
            elif kind == 'IDENT':
                if val in self.blacklist:
                    continue
                elif val in self.types:
                    if self.treat_types_as_operators.get():
                        operators_count[val] = operators_count.get(val, 0) + 1
                    else:
                        operands_count[val] = operands_count.get(val, 0) + 1
                elif val in all_funcs and self.treat_funcs_as_operators.get():
                    operators_count[val] = operators_count.get(val, 0) + 1
                elif val in self.keywords:
                    operators_count[val] = operators_count.get(val, 0) + 1
                else:
                    operands_count[val] = operands_count.get(val, 0) + 1

        self.update_results(operators_count, operands_count)

    def update_results(self, opers, opnds):
        for item in self.tree.get_children():
            self.tree.delete(item)

        sorted_opers = sorted(opers.items(), key=lambda x: x[1], reverse=True)
        sorted_opnds = sorted(opnds.items(), key=lambda x: x[1], reverse=True)

        eta1 = len(sorted_opers)
        N1 = sum(count for _, count in sorted_opers)
        
        eta2 = len(sorted_opnds)
        N2 = sum(count for _, count in sorted_opnds)

        max_len = max(eta1, eta2)
        for idx in range(max_len):
            row = []
            if idx < eta1:
                row.extend([idx + 1, sorted_opers[idx][0], sorted_opers[idx][1]])
            else:
                row.extend(["", "", ""])
            
            if idx < eta2:
                row.extend([idx + 1, sorted_opnds[idx][0], sorted_opnds[idx][1]])
            else:
                row.extend(["", "", ""])
                
            self.tree.insert("", tk.END, values=row)

        self.tree.insert("", tk.END, values=("---", "---", "---", "---", "---", "---"))
        self.tree.insert("", tk.END, values=("η1 =", eta1, f"N1 = {N1}", "η2 =", eta2, f"N2 = {N2}"))

        eta = eta1 + eta2
        N = N1 + N2
        V = N * math.log2(eta) if eta > 0 else 0

        self.lbl_dict.config(text=f"Словарь программы (η = η1 + η2): {eta}")
        self.lbl_len.config(text=f"Длина программы (N = N1 + N2): {N}")
        self.lbl_vol.config(text=f"Объем программы (V = N * log2(η)): {V:.2f} бит")

if __name__ == "__main__":
    root = tk.Tk()
    app = HalsteadParserApp(root)
    root.mainloop()