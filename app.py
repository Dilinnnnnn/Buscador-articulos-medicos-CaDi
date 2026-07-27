import os
from flask import Flask, render_template, request
from providers.factory import ProviderFactory

app = Flask(__name__)


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    source = request.args.get("source", "pubmed")
    page = max(1, request.args.get("page", 1, type=int))

    if not query:
        return render_template("index.html", selected_source=source)

    provider = ProviderFactory.get(source)
    result = provider.buscar(query, page)

    return render_template("resultados.html",
                           query=query,
                           articles=result.articles,
                           total=result.total,
                           page=result.page,
                           pages=result.pages,
                           source=result.source,
                           source_label=result.source_label,
                           selected_source=source,
                           error=result.error)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
