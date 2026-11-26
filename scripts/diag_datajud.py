#!/usr/bin/env python3
"""Diagnóstico leve do DataJud/STJ: identifica como aparecem os gabinetes e órgãos
(3ª e 4ª Turmas, 2ª Seção, Corte Especial) e mostra um exemplo de processo."""
import json, os, time, urllib.request, urllib.error
KEY=os.environ["DATAJUD_API_KEY"]
URL="https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
def q(body):
    for t in range(4):
        req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"APIKey "+KEY},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read())
        except urllib.error.HTTPError as e:
            print("HTTP",e.code); time.sleep(20*(t+1))
    return {"hits":{"hits":[],"total":{}}}
termos=["ANDRIGHI","VILLAS","BELLIZZE","MOURA RIBEIRO","ANTONIO CARLOS","BUZZI","SALOMÃO","NORONHA","RAUL ARAÚJO","GALLOTTI",
        "CUEVA","FERREIRA","TERCEIRA TURMA","QUARTA TURMA","SEGUNDA SEÇÃO","CORTE ESPECIAL","PRESIDÊNCIA","VICE-PRESIDÊNCIA"]
vistos={}
for t in termos:
    r=q({"size":20,"query":{"match_phrase":{"orgaoJulgador.nome":t}},"_source":["orgaoJulgador"],"sort":[{"dataHoraUltimaAtualizacao":{"order":"desc"}}]})
    print("BUSCA",t,"total",r["hits"].get("total"))
    for h in r["hits"]["hits"]:
        oj=h["_source"].get("orgaoJulgador",{});k=oj.get("codigo")
        if k not in vistos: vistos[k]=oj; print("ORGAO",json.dumps(oj,ensure_ascii=False))
    time.sleep(2)
# amostra: processos recentes, com órgãos variados
r=q({"size":60,"query":{"range":{"dataHoraUltimaAtualizacao":{"gte":"now-2d"}}},"_source":["orgaoJulgador","classe"]})
for h in r["hits"]["hits"]:
    oj=h["_source"].get("orgaoJulgador",{});k=oj.get("codigo")
    if k not in vistos: vistos[k]=oj; print("ORGAO_RECENTE",json.dumps(oj,ensure_ascii=False))
# um processo completo de gabinete de turma de direito privado
r=q({"size":1,"query":{"match_phrase":{"orgaoJulgador.nome":"ANDRIGHI"}},"sort":[{"dataHoraUltimaAtualizacao":{"order":"desc"}}]})
for h in r["hits"]["hits"]:
    s=h["_source"];mv=sorted(s.get("movimentos",[]),key=lambda m:m.get("dataHora",""))
    print("AMOSTRA",json.dumps({k:v for k,v in s.items() if k!="movimentos"},ensure_ascii=False)[:2500])
    for m in mv[-15:]: print("  MOV",json.dumps(m,ensure_ascii=False)[:260])
