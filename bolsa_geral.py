import requests
import base64
import time

requests.packages.urllib3.disable_warnings()

todos_os_dados = []
pagina = 1
tamanho = 120

while True:
    print(f"Baixando página {pagina}...")
    
    params = {"language": "pt-br", "pageNumber": pagina, "pageSize": tamanho}
    params_bytes = bytes(str(params), encoding="ascii")
    params_base64 = base64.b64encode(params_bytes).decode()
    url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/{params_base64}"
    
    response = requests.get(url, verify=False)
    data = response.json()
    
    resultados = data.get("results", [])
    if not resultados:
        break
        
    todos_os_dados.extend(resultados)
    
    total_paginas = data.get("page", {}).get("totalPages", 0)
    if pagina >= total_paginas:
        break
        
    pagina += 1
    time.sleep(0.5)

print(f"Total baixado: {len(todos_os_dados)} empresas")

# Ordena (opcional, mas recomendado)
todos_os_dados.sort(key=lambda x: x.get('issuingCompany', ''))

# Gera o TXT com "TICKER - ID"
with open('empresas_b3_ids_todas.txt', 'w', encoding='utf-8') as arquivo:
    for empresa in todos_os_dados:
        ticker = empresa.get('issuingCompany', '')
        code_cvm = empresa.get('codeCVM', '')
        if ticker and code_cvm:
            arquivo.write(f"{ticker} - {code_cvm}\n")

print("Arquivo 'empresas_b3_ids.txt' gerado com sucesso!")