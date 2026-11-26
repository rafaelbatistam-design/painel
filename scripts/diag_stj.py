import json, os, urllib.request, collections
KEY=os.environ.get("DATAJUD_API_KEY","")
URL="https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
def q(body):
    req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"APIKey "+KEY},method="POST")
    with urllib.request.urlopen(req,timeout=120) as r: return json.loads(r.read())
G="GABINETE DA MINISTRA NANCY ANDRIGHI"
print("== amostras Nancy, distribuidos recentes ==")
r=q({"size":3,"query":{"bool":{"must":[{"term":{"orgaoJulgador.nome.keyword":G}}]}},"sort":[{"dataAjuizamento":{"order":"desc"}}]})
print("total gabinete:", r["hits"]["total"])
for h in r["hits"]["hits"]:
    s=h["_source"]; m=s.pop("movimentos",[])
    print("KEYS", sorted(s.keys()))
    print(json.dumps(s,ensure_ascii=False)[:1500])
    for x in m: print("   MOV", x.get("dataHora"), x.get("codigo"), x.get("nome"), json.dumps(x.get("complementosTabelados",""),ensure_ascii=False)[:150], (x.get("orgaoJulgador") or {}).get("nome",""))
print("== classes (gabinetes 3a/4a, desde 2025) ==")
GABS=["GABINETE DA MINISTRA NANCY ANDRIGHI","GABINETE DO MINISTRO MOURA RIBEIRO","GABINETE DO MINISTRO RICARDO VILLAS BÔAS CUEVA","GABINETE DO MINISTRO HUMBERTO EUSTÁQUIO SOARES MARTINS","GABINETE DA MINISTRA DANIELA TEIXEIRA","GABINETE DA MINISTRA MARIA ISABEL GALLOTTI","GABINETE DO MINISTRO ANTONIO CARLOS FERREIRA","GABINETE DO MINISTRO JOÃO OTÁVIO DE NORONHA","GABINETE DO MINISTRO RAUL ARAÚJO FILHO","GABINETE DO MINISTRO MARCO BUZZI"]
r=q({"size":0,"query":{"bool":{"must":[{"terms":{"orgaoJulgador.nome.keyword":GABS}},{"range":{"dataAjuizamento":{"gte":"2025-01-01"}}}]}},"aggs":{"c":{"terms":{"field":"classe.nome.keyword","size":40}},"g":{"terms":{"field":"orgaoJulgador.nome.keyword","size":20}},"a":{"terms":{"field":"assuntos.nome.keyword","size":80}},"m":{"terms":{"field":"movimentos.nome.keyword","size":80}}}})
for k in ["g","c","a","m"]:
    print("--",k); [print(b["doc_count"],"|",b["key"]) for b in r["aggregations"][k]["buckets"]]
print("== Desembargador convocado Gambogi? ==")
r=q({"size":0,"query":{"wildcard":{"orgaoJulgador.nome.keyword":"*GAMBOGI*"}}}); print(r["hits"]["total"])
r=q({"size":0,"query":{"wildcard":{"orgaoJulgador.nome.keyword":"*BELLIZZE*"}},"aggs":{"y":{"date_histogram":{"field":"dataAjuizamento","calendar_interval":"year"}}}}); print("bellizze", r["hits"]["total"], [(b["key_as_string"][:4],b["doc_count"]) for b in r["aggregations"]["y"]["buckets"]][-4:])
print("== ultima atualizacao ==")
r=q({"size":0,"aggs":{"mx":{"max":{"field":"dataHoraUltimaAtualizacao"}}}}); print(r["aggregations"]["mx"])
