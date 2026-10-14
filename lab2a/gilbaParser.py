import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re


class GilbParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор метрик сложности Джилба")
        self.root.geometry("980x640")
        self.root.minsize(850, 550)
        self.setup_ui()

    def setup_ui(self):
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="Исходный код (Scala):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.text_area = tk.Text(left_frame, wrap=tk.NONE, width=42, font=("Consolas", 10))
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Загрузить файл", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Тестовый пример", command=self.load_sample).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Анализировать", command=self.analyze_code,
                  font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=5)

        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(right_frame, text="Таблица операторов и ветвлений:",
                 font=("Arial", 10, "bold")).pack(anchor="w")

        columns = ("j", "branch_op", "f_branch", "i", "gen_op", "f_gen")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        for col, w, anchor, txt in (
            ("j", 30, "center", "j"),
            ("branch_op", 140, "w", "Ветвление"),
            ("f_branch", 55, "center", "Кол-во"),
            ("i", 30, "center", "i"),
            ("gen_op", 140, "w", "Оператор языка"),
            ("f_gen", 55, "center", "Кол-во"),
        ):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.metrics_frame = tk.Frame(right_frame, pady=8)
        self.metrics_frame.pack(fill=tk.X)

        self.lbl_cl = tk.Label(self.metrics_frame, text="Абсолютная сложность (CL): —",
                               font=("Arial", 10, "bold"))
        self.lbl_cl.pack(anchor="w", pady=1)
        self.lbl_cli = tk.Label(self.metrics_frame, text="Максимальный уровень вложенности (CLI): —",
                                font=("Arial", 10, "bold"))
        self.lbl_cli.pack(anchor="w", pady=1)
        self.lbl_total = tk.Label(self.metrics_frame, text="Общее количество операторов (N): —",
                                  font=("Arial", 10))
        self.lbl_total.pack(anchor="w", pady=1)
        self.lbl_cl_rel = tk.Label(self.metrics_frame, text="Относительная сложность (cl = CL / N): —",
                                   font=("Arial", 10, "bold"), fg="#0044cc")
        self.lbl_cl_rel.pack(anchor="w", pady=1)

    def load_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Scala Files", "*.scala"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                code = file.read()
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, code)

    def load_sample(self):
        sample_code = """object SampleScalaApp {
  def main(args: Array[String]): Unit = {
    var x = 0
    var sum = 0
    while (x < 10) {
      if (x % 2 == 0) {
        sum += x
      }
      x += 1
    }
    var count = 0
    do {
      count += 1
    } while (count < 3)
    for (i <- 1 to 5) {
      i match {
        case 1 => println("One")
        case 2 => println("Two")
        case 3 => println("Three")
        case _ => println("Other")
      }
    }
    println(sum)
  }
}"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, sample_code)

    def remove_comments_and_strings(self, text: str) -> str:
        pattern = r'("""[\s\S]*?"""|"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//.*)'
        def replacer(match):
            s = match.group(0)
            if s.startswith('/') or s.startswith('"'):
                return '\n' * s.count('\n')
            return s
        return re.sub(pattern, replacer, text)

    # ---------- ЛОГИКА АНАЛИЗА ----------
    def analyze_code(self):
        raw_code = self.text_area.get(1.0, tk.END).strip()
        if not raw_code:
            messagebox.showwarning("Внимание", "Поле с кодом пусто.")
            return

        clean_code = self.remove_comments_and_strings(raw_code)

        tokens = re.findall(r'\b(if|else|while|do|for|match|case)\b|(=>|<-|;|\{|\}|_)',
                            clean_code)
        tokens = [t[0] or t[1] for t in tokens if t[0] or t[1]]

        branch_counts = {}
        current_nesting = 0
        max_cli = 0
        cl_total = 0
        brace_depth = 0
        scope_stack = []   # ('BRANCH',1) | ('BLOCK',0) | ('AWAIT_MATCH',0) | ('MATCH_BLOCK',[base, k])
        pending_do = []

        i, n = 0, len(tokens)
        while i < n:
            tok = tokens[i]

            if tok == 'if':
                cl_total += 1
                branch_counts['if'] = branch_counts.get('if', 0) + 1
                current_nesting += 1
                max_cli = max(max_cli, current_nesting)
                scope_stack.append(('BRANCH', 1))

            elif tok == 'for':
                cl_total += 1
                branch_counts['for'] = branch_counts.get('for', 0) + 1
                current_nesting += 1
                max_cli = max(max_cli, current_nesting)
                scope_stack.append(('BRANCH', 1))

            elif tok == 'while':
                if brace_depth in pending_do:
                    pending_do.remove(brace_depth)
                else:
                    cl_total += 1
                    branch_counts['while'] = branch_counts.get('while', 0) + 1
                    current_nesting += 1
                    max_cli = max(max_cli, current_nesting)
                    scope_stack.append(('BRANCH', 1))

            elif tok == 'do':
                cl_total += 1
                branch_counts['do-while'] = branch_counts.get('do-while', 0) + 1
                current_nesting += 1
                max_cli = max(max_cli, current_nesting)
                scope_stack.append(('BRANCH', 1))
                pending_do.append(brace_depth)

            elif tok == 'match':
                scope_stack.append(('AWAIT_MATCH', 0))

            elif tok == '{':
                brace_depth += 1
                if scope_stack and scope_stack[-1][0] == 'AWAIT_MATCH':
                    scope_stack.pop()
                    scope_stack.append(('MATCH_BLOCK', [current_nesting, 0]))
                else:
                    scope_stack.append(('BLOCK', 0))

            elif tok == '}':
                brace_depth -= 1
                if scope_stack:
                    top = scope_stack.pop()
                    if top[0] == 'MATCH_BLOCK':
                        base, k = top[1]
                        if k > 0:
                            max_cli = max(max_cli, base + k - 1)
                        current_nesting = base              
                    elif top[0] == 'BRANCH':
                        current_nesting -= 1
                while scope_stack and scope_stack[-1][0] == 'BRANCH':
                    scope_stack.pop()
                    current_nesting -= 1

            elif tok == 'case':
                # Находим ближайший MATCH_BLOCK
                match_idx = None
                for idx_rev, ctx in enumerate(reversed(scope_stack)):
                    if ctx[0] == 'MATCH_BLOCK':
                        match_idx = len(scope_stack) - 1 - idx_rev
                        break
                if match_idx is not None:
                    match_ctx = scope_stack[match_idx]
                    base = match_ctx[1][0]
                    
                    while len(scope_stack) > match_idx + 1:
                        scope_stack.pop()

                    is_default = (i + 1 < n and tokens[i + 1] == '_')
                    if not is_default:
                        match_ctx[1][1] += 1
                        case_idx = match_ctx[1][1]
                        cl_total += 1
                        branch_counts['case (условие)'] = branch_counts.get('case (условие)', 0) + 1
                        current_nesting = base + (case_idx - 1)        # <<< ГЛУБИНА ТЕЛА CASE
                    else:
                        k = match_ctx[1][1]
                        branch_counts['case _ (default)'] = branch_counts.get('case _ (default)', 0) + 1
                        current_nesting = base + max(k - 1, 0)         # <<< ГЛУБИНА DEFAULT
                    max_cli = max(max_cli, current_nesting)

            elif tok == ';':
                while scope_stack and scope_stack[-1][0] == 'BRANCH':
                    scope_stack.pop()
                    current_nesting -= 1

            i += 1

        # --- Подсчёт N (без изменений) ---
        def should_skip(line: str) -> bool:
            s = line.strip()
            if not s:
                return True
            if re.fullmatch(r'[{};]+', s):
                return True
            if re.match(r'^\}?\s*else\s*\{?\s*$', s):
                return True
            if re.match(r'^(object|class|trait|def|package|import)\b', s):
                return True
            return False

        general_ops_count = {}
        lines = [line.rstrip() for line in clean_code.split('\n')]
        in_do_block = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if in_do_block and (stripped.startswith('} while') or stripped.startswith('}while')):
                in_do_block = False
                continue
            if should_skip(stripped):
                continue
            stmts = [s.strip() for s in stripped.split(';') if s.strip()]
            for s in stmts:
                if not s or should_skip(s):
                    continue
                if 'match' in s and s.rstrip().endswith('{'):
                    op_type = 'селектор (match)'
                elif s.startswith('val ') or s.startswith('var '):
                    op_type = 'объявление (val/var)'
                elif re.search(r'\bif\b', s):
                    op_type = 'ветвление (if)'
                elif re.search(r'\bwhile\b', s):
                    op_type = 'цикл (while)'
                elif re.search(r'\bdo\b', s):
                    op_type = 'цикл (do-while)'
                    in_do_block = True
                elif re.search(r'\bfor\b', s):
                    op_type = 'цикл (for)'
                elif s.startswith('case '):
                    op_type = 'ветка выбора (case)'
                elif s.startswith('return ') or s.startswith('throw '):
                    op_type = 'возврат/ошибка'
                elif 'println' in s or 'print' in s:
                    op_type = 'вывод (print)'
                elif '=' in s:
                    op_type = 'присваивание (=)'
                else:
                    op_type = 'вызов/выражение'
                general_ops_count[op_type] = general_ops_count.get(op_type, 0) + 1

        self.update_results(branch_counts, general_ops_count, cl_total, max_cli)


    def update_results(self, branch_counts, gen_counts, cl_total, max_cli):
        for item in self.tree.get_children():
            self.tree.delete(item)

        sorted_branches = sorted(branch_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_gen = sorted(gen_counts.items(), key=lambda x: x[1], reverse=True)

        n_branches = len(sorted_branches)
        n_gen = len(sorted_gen)
        n_total_ops = sum(c for _, c in sorted_gen)

        for idx in range(max(n_branches, n_gen)):
            row = []
            if idx < n_branches:
                row.extend([idx + 1, sorted_branches[idx][0], sorted_branches[idx][1]])
            else:
                row.extend(["", "", ""])
            if idx < n_gen:
                row.extend([idx + 1, sorted_gen[idx][0], sorted_gen[idx][1]])
            else:
                row.extend(["", "", ""])
            self.tree.insert("", tk.END, values=row)

        self.tree.insert("", tk.END, values=(
            "CL =", cl_total, f"Σ={cl_total}",
            "N =", n_total_ops, f"Σ={n_total_ops}"
        ))

        cl_rel = round(cl_total / n_total_ops, 4) if n_total_ops > 0 else 0.0
        self.lbl_cl.config(text=f"Абсолютная сложность (CL): {cl_total}")
        self.lbl_cli.config(text=f"Максимальный уровень вложенности (CLI): {max_cli}")
        self.lbl_total.config(text=f"Общее количество операторов (N): {n_total_ops}")
        self.lbl_cl_rel.config(text=f"Относительная сложность (cl = CL / N): {cl_rel}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GilbParserApp(root)
    root.mainloop()