from app.services.fact_checker import search_and_verify
import json

text = "Donald Trump claims 6 Indian jets were shot down during May clash"
res = search_and_verify(text)
with open('test_res.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False)
