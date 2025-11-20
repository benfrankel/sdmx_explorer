QUERIES_PATH = "queries.txt"


def load():
    try:
        with open(QUERIES_PATH, "r") as f:
            return [q.strip() for q in f]
    except FileNotFoundError:
        return []


def save(query):
    queries = load()
    if query in queries:
        raise ValueError(f"There is already a saved query with this URL: {query}")
    queries.append(query)
    queries.sort()

    with open(QUERIES_PATH, "w") as f:
        f.writelines(q + "\n" for q in queries)
