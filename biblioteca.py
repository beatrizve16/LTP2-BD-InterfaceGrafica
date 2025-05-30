import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# ----- BANCO DE DADOS -----
# Conecta (ou cria) o arquivo biblioteca.db
conn = sqlite3.connect('biblioteca.db')
cursor = conn.cursor()

# Cria tabela autores (1:N com livros)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS autores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
''')

# Cria tabela livros, com FK para autores
cursor.execute('''
    CREATE TABLE IF NOT EXISTS livros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor_id INTEGER NOT NULL,
        ano INTEGER,
        FOREIGN KEY (autor_id) REFERENCES autores(id) ON DELETE CASCADE
    )
''')

conn.commit()

# ----- FUNÇÕES -----

def carregar_autores_combobox():
    """Carrega autores no combobox para seleção ao adicionar/editar livro."""
    cursor.execute("SELECT id, nome FROM autores ORDER BY nome")
    autores = cursor.fetchall()
    # Limpa combobox
    combo_autor['values'] = [autor[1] for autor in autores]
    # Guarda lista de ids para consulta
    combo_autor.ids = [autor[0] for autor in autores]

def adicionar_livro():
    """Adiciona novo livro no banco, cria autor se não existir."""
    titulo = entry_titulo.get().strip()
    autor_nome = combo_autor.get().strip()
    ano = entry_ano.get().strip()

    if not titulo or not autor_nome:
        messagebox.showwarning("Aviso", "Preencha título e autor.")
        return

    try:
        ano_int = int(ano) if ano else None
    except ValueError:
        messagebox.showerror("Erro", "Ano deve ser um número inteiro.")
        return

    # Verifica se autor existe, senão adiciona
    cursor.execute("SELECT id FROM autores WHERE nome = ?", (autor_nome,))
    autor = cursor.fetchone()
    if autor is None:
        cursor.execute("INSERT INTO autores (nome) VALUES (?)", (autor_nome,))
        conn.commit()
        autor_id = cursor.lastrowid
    else:
        autor_id = autor[0]

    # Insere livro
    cursor.execute("INSERT INTO livros (titulo, autor_id, ano) VALUES (?, ?, ?)",
                   (titulo, autor_id, ano_int))
    conn.commit()
    messagebox.showinfo("Sucesso", "Livro adicionado com sucesso!")
    limpar_campos()
    listar_livros()
    carregar_autores_combobox()

def listar_livros():
    """Lista todos os livros na treeview."""
    for item in tree.get_children():
        tree.delete(item)

    cursor.execute('''
        SELECT livros.id, livros.titulo, autores.nome, livros.ano
        FROM livros
        JOIN autores ON livros.autor_id = autores.id
        ORDER BY livros.titulo
    ''')

    for row in cursor.fetchall():
        tree.insert('', tk.END, values=row)

def selecionar_livro(event):
    """Ao selecionar um livro na tabela, preenche os campos para edição/deleção."""
    selecionado = tree.focus()
    if selecionado:
        valores = tree.item(selecionado, 'values')
        entry_id.delete(0, tk.END)
        entry_titulo.delete(0, tk.END)
        combo_autor.set('')
        entry_ano.delete(0, tk.END)

        entry_id.insert(0, valores[0])
        entry_titulo.insert(0, valores[1])
        combo_autor.set(valores[2])
        entry_ano.insert(0, valores[3] if valores[3] is not None else '')

def atualizar_livro():
    """Atualiza dados do livro selecionado."""
    livro_id = entry_id.get()
    titulo = entry_titulo.get().strip()
    autor_nome = combo_autor.get().strip()
    ano = entry_ano.get().strip()

    if not livro_id or not titulo or not autor_nome:
        messagebox.showwarning("Aviso", "Selecione um livro e preencha título e autor.")
        return

    try:
        ano_int = int(ano) if ano else None
    except ValueError:
        messagebox.showerror("Erro", "Ano deve ser um número inteiro.")
        return

    # Verifica/insere autor
    cursor.execute("SELECT id FROM autores WHERE nome = ?", (autor_nome,))
    autor = cursor.fetchone()
    if autor is None:
        cursor.execute("INSERT INTO autores (nome) VALUES (?)", (autor_nome,))
        conn.commit()
        autor_id = cursor.lastrowid
    else:
        autor_id = autor[0]

    cursor.execute("UPDATE livros SET titulo = ?, autor_id = ?, ano = ? WHERE id = ?",
                   (titulo, autor_id, ano_int, livro_id))
    if cursor.rowcount == 0:
        messagebox.showerror("Erro", "Livro não encontrado.")
    else:
        conn.commit()
        messagebox.showinfo("Sucesso", "Livro atualizado com sucesso!")
        limpar_campos()
        listar_livros()
        carregar_autores_combobox()

def deletar_livro():
    """Deleta livro selecionado."""
    livro_id = entry_id.get()
    if not livro_id:
        messagebox.showwarning("Aviso", "Selecione um livro para deletar.")
        return

    confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja deletar este livro?")
    if confirm:
        cursor.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
        if cursor.rowcount == 0:
            messagebox.showerror("Erro", "Livro não encontrado.")
        else:
            conn.commit()
            messagebox.showinfo("Sucesso", "Livro deletado com sucesso!")
            limpar_campos()
            listar_livros()
            carregar_autores_combobox()

def limpar_campos():
    """Limpa todos os campos do formulário."""
    entry_id.delete(0, tk.END)
    entry_titulo.delete(0, tk.END)
    combo_autor.set('')
    entry_ano.delete(0, tk.END)

# ----- INTERFACE GRÁFICA -----
janela = tk.Tk()
janela.title("Biblioteca")
janela.geometry("700x450")
janela.resizable(False, False)

# Labels e Entrys
tk.Label(janela, text="ID").grid(row=0, column=0, padx=5, pady=5)
entry_id = tk.Entry(janela)
entry_id.grid(row=0, column=1, padx=5, pady=5)
entry_id.config(state='readonly')  # ID não editável

tk.Label(janela, text="Título").grid(row=1, column=0, padx=5, pady=5)
entry_titulo = tk.Entry(janela, width=40)
entry_titulo.grid(row=1, column=1, padx=5, pady=5)

tk.Label(janela, text="Autor").grid(row=2, column=0, padx=5, pady=5)
combo_autor = ttk.Combobox(janela, width=37)
combo_autor.grid(row=2, column=1, padx=5, pady=5)

tk.Label(janela, text="Ano").grid(row=3, column=0, padx=5, pady=5)
entry_ano = tk.Entry(janela)
entry_ano.grid(row=3, column=1, padx=5, pady=5)

# Botões
btn_adicionar = tk.Button(janela, text="Adicionar", command=adicionar_livro)
btn_adicionar.grid(row=0, column=2, padx=5, pady=5)

btn_atualizar = tk.Button(janela, text="Atualizar", command=atualizar_livro)
btn_atualizar.grid(row=1, column=2, padx=5, pady=5)

btn_deletar = tk.Button(janela, text="Deletar", command=deletar_livro)
btn_deletar.grid(row=2, column=2, padx=5, pady=5)

btn_limpar = tk.Button(janela, text="Limpar", command=limpar_campos)
btn_limpar.grid(row=3, column=2, padx=5, pady=5)

# Treeview (tabela)
colunas = ('ID', 'Título', 'Autor', 'Ano')
tree = ttk.Treeview(janela, columns=colunas, show='headings', height=15)
for col in colunas:
    tree.heading(col, text=col)
tree.column('ID', width=40, anchor='center')
tree.column('Título', width=300)
tree.column('Autor', width=150)
tree.column('Ano', width=60, anchor='center')

tree.grid(row=4, column=0, columnspan=3, padx=10, pady=10)
tree.bind('<<TreeviewSelect>>', selecionar_livro)

# Carrega autores para combobox e lista livros na tabela
carregar_autores_combobox()
listar_livros()

janela.mainloop()

# Fecha conexão com banco ao fechar programa
conn.close()
