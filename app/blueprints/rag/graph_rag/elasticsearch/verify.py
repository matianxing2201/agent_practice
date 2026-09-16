from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=["http://127.0.0.1:9200"],
    verify_certs=False,
    request_timeout=60
)

print("ping ->" , es.ping())
print("version ->", es.info()["version"]["number"])