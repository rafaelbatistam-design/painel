import json, os, urllib.request, collections
KEY=os.environ.get("DATAJUD_API_KEY","")
URL="https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
import time, urllib.error
def q(body):
    for t in range(6):
        req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"APIKey "+KEY},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=120) as r: return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(20*(t+1)); continue
            print("HTTP",e.code,e.read()[:300]); raise
    raise SystemExit("429 persistente")

GABS={"Nancy Andrighi":"*NANCY ANDRIGHI*","Moura Ribeiro":"*MOURA RIBEIRO*","Villas Bôas Cueva":"*CUEVA*","Humberto Martins":"*HUMBERTO*MARTINS*","Daniela Teixeira":"*DANIELA TEIXEIRA*",
 "Isabel Gallotti":"*ISABEL GALLOTTI*","Antonio Carlos Ferreira":"*ANTONIO CARLOS FERREIRA*","Noronha":"*NORONHA*","Raul Araújo":"*RAUL ARA*","Marco Buzzi":"*MARCO BUZZI*","Gambogi":"*GAMBOGI*"}
FIM=["Trânsito em julgado","Baixa Definitiva","Definitivo"]
DEC=["Não Conhecimento de recurso","Não-Provimento","Provimento","Provimento em Parte","Conhecimento para não conhecer do Recurso Especial","Conhecimento em Parte e Não-Provimento ou Denegação","conhecimento para conhecer em parte o recurso especial e negar provimento","Conhecimento para negar provimento ao recurso especial","Recurso prejudicado","Conhecimento para dar provimento ao Recurso Especial ","conhecimento para dar parcial provimento ao recurso especial","Desistência","Homologação de Transação","Declaração de competência em conflito","Não conhecimento do pedido","Indeferimento","Extinção","Negação de seguimento","Prejudicado"]
tot=[0,0,0]
for nome,pat in GABS.items():
    base=[{"wildcard":{"orgaoJulgador.nome.keyword":pat}},{"range":{"movimentos.dataHora":{"gte":"2025-11-26"}}}]
    a=q({"size":0,"track_total_hits":True,"query":{"bool":{"must":base}}})["hits"]["total"]["value"]
    b=q({"size":0,"track_total_hits":True,"query":{"bool":{"must":base,"must_not":[{"terms":{"movimentos.nome.keyword":FIM}}]}}})["hits"]["total"]["value"]
    c=q({"size":0,"track_total_hits":True,"query":{"bool":{"must":base,"must_not":[{"terms":{"movimentos.nome.keyword":FIM+DEC}}]}}})["hits"]["total"]["value"]
    print(f"{nome}: com movimento em 12m={a} | sem baixa/transito={b} | sem decisao={c}"); tot[0]+=a;tot[1]+=b;tot[2]+=c
print("TOTAL",tot)
r=q({"size":2,"query":{"bool":{"must":[{"wildcard":{"orgaoJulgador.nome.keyword":"*NANCY ANDRIGHI*"}},{"range":{"movimentos.dataHora":{"gte":"2026-10-01"}}}],"must_not":[{"terms":{"movimentos.nome.keyword":FIM+DEC}}]}},"_source":["numeroProcesso","classe","dataAjuizamento","assuntos","orgaoJulgador","grau","formato","sistema","nivelSigilo","id"]})
for h in r["hits"]["hits"]: print("SAMPLE", h.get("_id"), json.dumps(h["_source"],ensure_ascii=False)[:900])
r=q({"size":1,"query":{"bool":{"must":[{"wildcard":{"orgaoJulgador.nome.keyword":"*NANCY ANDRIGHI*"}},{"range":{"movimentos.dataHora":{"gte":"2026-10-01"}}}]}},"_source":["movimentos"]})
for m in r["hits"]["hits"][0]["_source"]["movimentos"]: print("MOV",m.get("dataHora"),m.get("codigo"),m.get("nome"),(m.get("orgaoJulgador") or {}).get("nome",""),json.dumps(m.get("complementosTabelados",""),ensure_ascii=False)[:120])
