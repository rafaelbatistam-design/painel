#!/usr/bin/env python3
"""Diagnóstico do DataJud/STJ: lista os órgãos julgadores e mostra um exemplo de
processo, para calibrar o Monitor STJ. Só lê dados públicos e imprime no log."""
import json, os, urllib.request
KEY=os.environ["DATAJUD_API_KEY"]
URL="https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
def q(body):
    req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"APIKey "+KEY},method="POST")
    with urllib.request.urlopen(req,timeout=90) as r: return json.loads(r.read())
# 1) órgãos julgadores com movimento no último ano
r=q({"size":0,"query":{"range":{"movimentos.dataHora":{"gte":"now-365d"}}},
     "aggs":{"o":{"terms":{"field":"orgaoJulgador.codigo","size":400},
       "aggs":{"n":{"top_hits":{"size":1,"_source":["orgaoJulgador"]}}}}}})
print("TOTAL_ULTIMO_ANO",r["hits"]["total"])
for b in r["aggregations"]["o"]["buckets"]:
    oj=b["n"]["hits"]["hits"][0]["_source"].get("orgaoJulgador",{})
    print("ORGAO",b["key"],b["doc_count"],json.dumps(oj,ensure_ascii=False))
# 2) amostra completa de um processo recente
r=q({"size":2,"query":{"range":{"movimentos.dataHora":{"gte":"now-30d"}}},"sort":[{"dataHoraUltimaAtualizacao":{"order":"desc"}}]})
for h in r["hits"]["hits"]:
    s=h["_source"];mv=sorted(s.get("movimentos",[]),key=lambda m:m.get("dataHora",""))
    s2={k:v for k,v in s.items() if k!="movimentos"}
    print("AMOSTRA",json.dumps(s2,ensure_ascii=False)[:1500])
    for m in mv[-12:]: print("  MOV",json.dumps(m,ensure_ascii=False)[:300])
# 3) códigos de movimento mais comuns (para identificar julgado, baixa, trânsito)
r=q({"size":0,"query":{"range":{"movimentos.dataHora":{"gte":"now-90d"}}},
     "aggs":{"m":{"terms":{"field":"movimentos.codigo","size":80},"aggs":{"n":{"top_hits":{"size":1,"_source":["movimentos.codigo","movimentos.nome"]}}}}}})
for b in r["aggregations"]["m"]["buckets"]:
    nomes={m.get("codigo"):m.get("nome") for m in b["n"]["hits"]["hits"][0]["_source"].get("movimentos",[])}
    print("MOVCOD",b["key"],b["doc_count"],nomes.get(b["key"]))
