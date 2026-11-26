#!/usr/bin/env python3
"""
Monitor STJ · Marquez Advogados
Processos de direito privado pendentes de julgamento na 3ª e 4ª Turmas e na 2ª Seção.
Fonte: API pública do DataJud (CNJ). Gera stj/data.js e stj/index.html.
"""
import json, os, sys, time, unicodedata, urllib.request, urllib.error
from datetime import datetime, date, timedelta

API_KEY = os.environ.get("DATAJUD_API_KEY", "")
API_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
MESES = 12

# Composição atual (guias do STJ: 3ª Turma, ago/2026; 4ª Turma, set/2026).
# Cada entrada: nome exibido, turma, trecho que identifica o gabinete na base do CNJ.
MINISTROS = [
    ("Daniela Teixeira",        "3ª Turma", "DANIELA TEIXEIRA"),
    ("Ricardo Villas Bôas Cueva","3ª Turma", "CUEVA"),
    ("Moura Ribeiro",           "3ª Turma", "MOURA RIBEIRO"),
    ("Humberto Martins",        "3ª Turma", "HUMBERTO EUSTAQUIO SOARES MARTINS"),
    ("Nancy Andrighi",          "3ª Turma", "NANCY ANDRIGHI"),
    ("Maria Isabel Gallotti",   "4ª Turma", "MARIA ISABEL GALLOTTI"),
    ("Antonio Carlos Ferreira", "4ª Turma", "ANTONIO CARLOS FERREIRA"),
    ("João Otávio de Noronha",  "4ª Turma", "NORONHA"),
    ("Raul Araújo",             "4ª Turma", "RAUL ARAUJO"),
    ("Luís Carlos Gambogi (convocado)", "4ª Turma", "GAMBOGI"),
    ("Marco Buzzi",             "4ª Turma", "MARCO BUZZI"),
]

# Classes julgadas pela 2ª Seção quando vêm de relator da 3ª/4ª Turma
CLASSES_SECAO = {"Conflito de Competência", "Embargos de Divergência em Recurso Especial",
                 "Embargos de Divergência em Agravo em Recurso Especial", "Reclamação", "Ação Rescisória"}
CLASSES_FORA = {"Habeas Corpus", "Recurso Ordinário em Habeas Corpus", "Ação Penal", "Inquérito",
                "Pedido de Uniformização de Interpretação de Lei Criminal", "Embargos de Terceiro Criminal",
                "Carta Rogatória", "Sentença Estrangeira", "Intervenção Federal", "Habeas Data", "Mandado de Injunção"}

FIM = ["Trânsito em julgado", "Baixa Definitiva", "Definitivo"]
DECISOES = ["Não Conhecimento de recurso", "Não-Provimento", "Provimento", "Provimento em Parte",
    "Conhecimento para não conhecer do Recurso Especial", "Conhecimento em Parte e Não-Provimento ou Denegação",
    "conhecimento para conhecer em parte o recurso especial e negar provimento",
    "Conhecimento para negar provimento ao recurso especial", "Recurso prejudicado",
    "Conhecimento para dar provimento ao Recurso Especial ", "conhecimento para dar parcial provimento ao recurso especial",
    "Desistência", "Homologação de Transação", "Declaração de competência em conflito", "Não conhecimento do pedido",
    "Indeferimento", "Extinção", "Negação de seguimento", "Prejudicado", "Desistência de Recurso",
    "Conhecimento em Parte e Provimento em Parte ou Concessão em Parte", "Conhecimento em Parte e Provimento ou Concessão",
    "conhecimento para conhecer em parte o recurso especial e dar provimento ", "Improcedência", "Procedência",
    "Indeferimento da petição inicial", "Provimento (art. 557 do CPC)", "Incompetência"]

# Matérias fora da atuação do escritório: processo sai se TODOS os assuntos forem destas matérias.
FORA = ["tribut", "imposto", "icms", "iss ", "ipi", "pis", "cofins", "contribui", "execução fiscal", "crédito tributário",
        "trabalh", "fgts", "vínculo empregat", "horas extras", "verbas rescisórias",
        "previdenciári", "aposentadoria", "auxílio-doença", "benefício assistencial", "pensão por morte",
        "penal", "crime", "pena ", "prisão", "tráfico", "homicídio", "furto", "roubo",
        "servidor público", "concurso público", "licitação", "improbidade", "eleitoral", "militar"]

# Áreas de atuação, da mais específica para a mais geral (palavras em minúsculas, sem acento)
AREAS = [
    ("Arbitragem", ["arbitra", "compromissori", "dispute board"]),
    ("Societário e empresarial", ["societ", "socio", "quota", "haveres", "dissolucao", "acionist", "assembleia",
        "desconsideracao da personalidade", "recuperacao judicial", "falencia", "classificacao de creditos",
        "concurso de credores", "empresari", "holding", "estabelecimento", "fundo de comercio", "franquia", "associacao"]),
    ("Propriedade intelectual", ["marca", "patente", "propriedade intelectual", "industrial", "direito autoral",
        "software", "concorrencia desleal", "nome empresarial", "desenho industrial", "programa de computador"]),
    ("Família e sucessões", ["inventario", "partilha", "heranca", "sucess", "testament", "legado", "uniao estavel",
        "divorcio", "alimentos", "guarda", "regime de bens", "casamento", "filiacao", "paternidade", "curatela",
        "tutela de menor", "bem de familia", "doacao", "colacao", "meacao", "familia"]),
    ("Imobiliário e construção", ["imovel", "imobili", "incorporacao", "vicios de construcao", "construcao", "empreitada",
        "locacao", "despejo", "aluguel", "condomin", "usucapiao", "posse", "esbulho", "turbacao", "reivindica",
        "imissao", "propriedade", "loteamento", "registro de imoveis", "servidao", "superficie", "promessa de compra e venda",
        "adjudicacao compulsoria", "direito de vizinhanca", "leilao", "arrematacao", "corretagem"]),
    ("Títulos de crédito e execução", ["titulo", "cheque", "duplicata", "nota promissoria", "letra de cambio",
        "cedula de credito", "execucao", "penhora", "embargos a execucao", "cumprimento de sentenca",
        "cumprimento provisorio", "impenhorabilidade", "expropria", "fraude a execucao", "fraude contra credores"]),
    ("Bancário e financeiro", ["bancari", "juros", "capitalizacao", "anatocismo", "cartao de credito", "emprestimo",
        "mutuo", "financiamento", "alienacao fiduciaria", "consorcio", "expurgos", "conta corrente", "tarifa",
        "credito rural", "investimento", "mercado de capitais", "valores mobiliarios"]),
    ("Saúde suplementar, seguros e previdência privada", ["plano de saude", "planos de saude", "seguro", "previdencia privada",
        "tratamento medico", "medicamento", "home care", "reajuste"]),
    ("Contratos", ["contrat", "compra e venda", "prestacao de servicos", "fornecimento", "distribuicao", "representacao comercial",
        "inadimplemento", "rescisao", "resolucao", "clausula", "multa", "onerosidade", "revisao", "arras", "fianca",
        "cessao", "transporte", "mandato", "comodato", "leasing", "arrendamento", "factoring", "take or pay",
        "obrigac", "pagamento", "adimplemento", "confissao", "composicao de divida", "perdas e danos"]),
    ("Responsabilidade civil", ["dano moral", "dano material", "dano estetico", "indenizacao", "responsabilidade civil",
        "erro medico", "acidente", "direito de imagem", "honra", "lucros cessantes", "perda de uma chance"]),
    ("Consumidor", ["consumidor", "praticas abusivas", "clausulas abusivas", "cadastro de inadimplentes",
        "inclusao indevida", "dever de informacao", "vicio do produto", "fato do produto", "estabelecimentos de ensino",
        "repeticao do indebito", "cobranca indevida"]),
    ("Honorários advocatícios", ["honorarios", "servicos profissionais", "sucumbenc"]),
    ("Processo civil", ["prescricao", "decadencia", "competencia", "provas", "onus da prova", "tutela", "liminar",
        "efeito suspensivo", "assistencia judiciaria", "gratuidade", "coisa julgada", "rescisoria", "nulidade",
        "intervencao de terceiros", "litisconsorcio", "legitimidade", "recurso", "jurisdicao"]),
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()

def post_api(body):
    if not API_KEY:
        log("ERRO: chave do DataJud ausente."); sys.exit(1)
    payload = json.dumps(body).encode("utf-8")
    for tentativa in range(7):
        req = urllib.request.Request(API_URL, data=payload, method="POST",
              headers={"Content-Type": "application/json", "Authorization": f"APIKey {API_KEY}"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                espera = 20 * (tentativa + 1); log(f"  HTTP {e.code}, nova tentativa em {espera}s"); time.sleep(espera); continue
            log(f"  HTTP {e.code}: {e.read().decode(errors='ignore')[:200]}"); return None
        except Exception as e:
            espera = 15 * (tentativa + 1); log(f"  Erro {e}, nova tentativa em {espera}s"); time.sleep(espera)
    log("  Falhou após várias tentativas."); return None

def nomes_gabinetes():
    """Descobre o nome exato de cada gabinete na base (o nome traz acentos e varia)."""
    dados = post_api({"size": 0, "query": {"range": {"dataAjuizamento": {"gte": "2024-01-01"}}},
                      "aggs": {"g": {"terms": {"field": "orgaoJulgador.nome.keyword", "size": 300}}}})
    chaves = [b["key"] for b in (dados or {}).get("aggregations", {}).get("g", {}).get("buckets", [])]
    achados = {}
    for nome, turma, trecho in MINISTROS:
        alvo = sem_acento(trecho)
        hits = [k for k in chaves if alvo in sem_acento(k) and ("GABINETE" in k.upper() or "DESEMBARGADOR" in k.upper())]
        if hits:
            achados[nome] = (turma, hits)
            log(f"  {nome}: {hits}")
        else:
            log(f"  {nome}: gabinete não encontrado na base")
    return achados

def area_de(assuntos):
    txt = " | ".join(sem_acento(a) for a in assuntos)
    for area, chaves in AREAS:
        if any(c in txt for c in chaves):
            return area
    return "Outros (direito privado)"

def fora_da_atuacao(assuntos):
    if not assuntos: return False
    return all(any(f in sem_acento(a) for f in FORA) for a in assuntos)

def situacao(movs):
    nomes = [(m.get("dataHora", ""), (m.get("nome") or "").strip()) for m in movs]
    nomes.sort()
    pauta = None
    for d, n in nomes:
        if n == "Inclusão em pauta": pauta = d
        elif n in ("Retirada de pauta", "Retirada") and pauta: pauta = None
    if pauta: return "Em pauta", pauta[:10]
    return "Aguardando julgamento", ""

def coletar():
    desde = (date.today() - timedelta(days=int(MESES * 30.5))).isoformat()
    log("=== Gabinetes ===")
    gabs = nomes_gabinetes()
    procs, vistos = [], set()
    for nome, (turma, chaves) in gabs.items():
        must = [{"terms": {"orgaoJulgador.nome.keyword": chaves}},
                {"range": {"movimentos.dataHora": {"gte": desde}}}]
        must_not = [{"terms": {"movimentos.nome.keyword": FIM + DECISOES}},
                    {"terms": {"classe.nome.keyword": sorted(CLASSES_FORA)}}]
        after, total = None, 0
        while True:
            body = {"size": 500, "query": {"bool": {"must": must, "must_not": must_not}},
                    "_source": ["numeroProcesso", "classe", "assuntos", "movimentos", "dataAjuizamento", "orgaoJulgador"],
                    "sort": [{"@timestamp": {"order": "asc"}}]}
            if after: body["search_after"] = after
            dados = post_api(body)
            if not dados: break
            hits = dados.get("hits", {}).get("hits", [])
            for h in hits:
                s = h.get("_source", {})
                num = s.get("numeroProcesso", "")
                if not num or num in vistos: continue
                classe = (s.get("classe") or {}).get("nome", "")
                assuntos = [a.get("nome", "").strip() for a in (s.get("assuntos") or []) if isinstance(a, dict) and a.get("nome")]
                if fora_da_atuacao(assuntos): continue
                movs = s.get("movimentos") or []
                datas = sorted(m.get("dataHora", "") for m in movs if m.get("dataHora"))
                distrib = [m.get("dataHora", "") for m in movs if (m.get("nome") or "") in ("Distribuição", "Redistribuição", "Redistribuição por prevenção")]
                chegada = (min(distrib) if distrib else (datas[0] if datas else ""))[:10]
                if chegada and chegada < desde: continue
                ult = max(movs, key=lambda m: m.get("dataHora", "")) if movs else {}
                sit, data_pauta = situacao(movs)
                orgao = "2ª Seção" if classe in CLASSES_SECAO else turma
                vistos.add(num)
                procs.append([num, classe, orgao, nome, area_de(assuntos), assuntos, chegada, sit, data_pauta,
                              (ult.get("nome") or "").strip(), (ult.get("dataHora") or "")[:10]])
                total += 1
            if len(hits) < 500: break
            after = hits[-1].get("sort")
            time.sleep(1.0)
        log(f"  {nome}: {total} processos")
        time.sleep(2.0)
    procs.sort(key=lambda p: p[6], reverse=True)
    return procs

def main():
    procs = coletar()
    if not procs:
        log("Nenhum processo coletado; mantendo a página anterior."); sys.exit(1)
    # tabela de assuntos para deixar o arquivo leve
    tab = sorted({a for p in procs for a in p[5]})
    idx = {a: i for i, a in enumerate(tab)}
    linhas = [[p[0], p[1], p[2], p[3], p[4], [idx[a] for a in p[5]], p[6], p[7], p[8], p[9], p[10]] for p in procs]
    agora = datetime.utcnow() - timedelta(hours=3)
    meta = {"atualizado": agora.strftime("%d/%m/%Y %H:%M"), "meses": MESES, "total": len(linhas)}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stj")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.STJ_META=" + json.dumps(meta, ensure_ascii=False) + ";\n")
        f.write("window.STJ_ASSUNTOS=" + json.dumps(tab, ensure_ascii=False) + ";\n")
        f.write("window.STJ_DADOS=" + json.dumps(linhas, ensure_ascii=False, separators=(",", ":")) + ";\n")
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stj_pagina.html"), encoding="utf-8").read()
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(tpl.replace("__VERSAO__", agora.strftime("%Y%m%d%H%M")))
    log(f"Gravado: {len(linhas)} processos, {len(tab)} assuntos")

if __name__ == "__main__":
    main()
