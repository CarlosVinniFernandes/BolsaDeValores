import requests
import base64
import time

requests.packages.urllib3.disable_warnings()

# ========== FUNÇÃO DE VALIDAÇÃO DE CNPJ ==========
def validar_cnpj(cnpj):
    if not cnpj or not isinstance(cnpj, str):
        return False

    # A API da B3 devolve o CNPJ sem os zeros à esquerda (ex.: AMBEV vem
    # como '7526557000100'), então completa até 14 dígitos antes de validar
    cnpj = cnpj.strip().zfill(14)

    if len(cnpj) != 14 or not cnpj.isdigit():
        return False

    if len(set(cnpj)) == 1:
        return False

    # Primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    if int(cnpj[12]) != digito1:
        return False

    # Segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    if int(cnpj[13]) != digito2:
        return False

    return True

# ========== BAIXAR OS DADOS ==========
todos_os_dados = []
pagina = 1
tamanho = 120  # Máximo permitido pela B3

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

print(f"Total bruto baixado: {len(todos_os_dados)} empresas")

# ========== FILTROS ==========
# Campos da API (todos vêm como STRING):
#   type            '1' = companhia emissora de ações
#                   '4' = BDR, '7' = não negociada em bolsa, '6'/'2' = outros
#   marketIndicator '18' = Novo Mercado, '17' = Nível 2, '16' = Nível 1,
#                   '1'  = segmento tradicional/básico (ex.: AMBEV)
#                   '7'  = mercado de balcão (MB), '8' = emissores só de
#                   dívida/debêntures (sem ação negociada), '99' = sem mercado
SEGMENTOS_BOLSA = {'1', '16', '17', '18'}

empresas_acoes = []
for emp in todos_os_dados:
    if not validar_cnpj(emp.get('cnpj', '')):
        continue

    if emp.get('status') != 'A':
        continue

    if emp.get('type') != '1':
        continue

    if emp.get('marketIndicator') not in SEGMENTOS_BOLSA:
        continue

    empresas_acoes.append(emp)

print(f"Empresas com ações negociadas em bolsa: {len(empresas_acoes)}")

# Agrupa por CNPJ para evitar duplicatas
cnpjs_vistos = set()
empresas_unicas = []
for emp in empresas_acoes:
    cnpj = emp.get('cnpj')
    if cnpj not in cnpjs_vistos:
        cnpjs_vistos.add(cnpj)
        empresas_unicas.append(emp)

print(f"Empresas únicas (agrupadas por CNPJ): {len(empresas_unicas)}")

# ========== ORDENA E SALVA O TXT ==========
empresas_unicas.sort(key=lambda x: x.get('issuingCompany', ''))

with open('empresas_b3_ids.txt', 'w', encoding='utf-8') as arquivo:
    for empresa in empresas_unicas:
        ticker = empresa.get('issuingCompany', '')
        code_cvm = empresa.get('codeCVM', '')
        if ticker and code_cvm:
            arquivo.write(f"{ticker} - {code_cvm}\n")

print("Arquivo 'empresas_b3_ids.txt' gerado com sucesso!")
