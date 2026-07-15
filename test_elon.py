from app.services.fact_checker import search_and_verify

text = "Elon Musk announces he is buying Disney to delete the Star Wars franchise."
res = search_and_verify(text)
print(res)
