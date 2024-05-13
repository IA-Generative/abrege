

For method='refine', metrics=[0.5263157894736842, 0.38461538461538464, 0.36363636363636365, 0.3076923076923077, 0.6923076923076923], rmetrics=[0.0, 0.0, 1.0, 0.0, 1.0]
method='refine' statistics.mean(metrics)=0.45491350754508647 [0.5263157894736842, 0.38461538461538464, 0.36363636363636365, 0.3076923076923077, 0.6923076923076923]

  0%|                                                                                                                             | 0/5 [00:00<?, ?it/s]Calcul des résumés...
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 5/5 [07:27<00:00, 89.54s/it]
done
For method='map_reduce', metrics=[0.6, 0.4, 0.8333333333333334, 0.5454545454545454, 0.22580645161290322], rmetrics=[0.0, 1.0, 0.0, 1.0, 0.0]
method='map_reduce' statistics.mean(metrics)=0.5209188660801564 [0.6, 0.4, 0.8333333333333334, 0.5454545454545454, 0.22580645161290322]

method='refine' statistics.mean(metrics)=0.45491350754508647 [0.5263157894736842, 0.38461538461538464, 0.36363636363636365, 0.3076923076923077, 0.6923076923076923]
method='map_reduce' statistics.mean(metrics)=0.5209188660801564 [0.6, 0.4, 0.8333333333333334, 0.5454545454545454, 0.22580645161290322]

done
For method='text_rank', metrics=[0.8333333333333334, 1.0, 1.0, 0.6, 1.0], rmetrics=[0.0, 1.0, 0.0, 0.0, 0.0]
method='text_rank' statistics.mean(metrics)=0.8866666666666667 [0.8333333333333334, 1.0, 1.0, 0.6, 1.0]

method='text_rank' statistics.mean(metrics)=0.8866666666666667 [0.8333333333333334, 1.0, 1.0, 0.6, 1.0]



---

usage

poetry export -f requirements.txt --without-hashes > requirements.txt


sys.path.append(str(Path("abrege").absolute()))

https://docs.trychroma.com/troubleshooting#sqlite

uvicorn app.main:app --host 0.0.0.0 --port 8000


openai = "^1.23.1"
ipykernel = "^6.29.4"
langchain-openai = "^0.1.3"
sentence-transformers = "^2.7.0"
fastapi = "^0.110.2"
networkx = {extras = ["default"], version = "^3.3"}
py-pdf-parser = "^0.12.0"
ipywidgets = "^8.1.2"
pytest = "^8.1.1"
httpx = "^0.27.0"
nltk = "^3.8.1"
unstructured = "^0.13.4"
datasets = "^2.19.0"
langchain-community = "^0.0.34"
langchain-core = "^0.1.46"
tiktoken = "^0.6.0"
chromadb = "^0.5.0"