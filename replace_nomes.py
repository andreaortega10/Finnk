import glob
files = glob.glob('frontend/src/**/*.jsx', recursive=True)
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    content = content.replace("'Dashboard'", "'Análise Geral'")
    content = content.replace(">Dashboard<", ">Análise Geral<")
    content = content.replace("label: 'Dashboard'", "label: 'Análise Geral'")
    
    content = content.replace("'Compromissos'", "'Despesas'")
    content = content.replace(">Compromissos<", ">Despesas<")
    content = content.replace("label: 'Compromissos'", "label: 'Despesas'")
    
    content = content.replace("'Entradas'", "'Receitas'")
    content = content.replace(">Entradas<", ">Receitas<")
    content = content.replace("label: 'Entradas'", "label: 'Receitas'")
    
    content = content.replace("& Entradas", "& Receitas")
    content = content.replace("Transações & Entradas", "Transações & Receitas")
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
