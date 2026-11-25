# Anticipatory Commerce: starter kit

Rezolve AI × Techfest, IIT Bombay 2026–27, Problem Statement 1.

A shopping request arrives one word at a time: *"black running shoes, size nine, under two
thousand…"*. Build an agent that predicts the shopper's filters from the words so far, searches
early, and commits to the right product as soon as it is safe to, without ever committing to a
wrong one.

Python 3.9 or later, standard library only. Nothing to install.

```
python evaluate.py                         # score the baseline on dev.jsonl
python evaluate.py --agent my_agent.py     # score your agent
python search.py white Pacevo sneakers     # try the local search
```

## What's in the kit

| File | What it is |
|---|---|
| `catalogue.csv` | 1,074 products: `product_id, title, brand, category, colour, size, price, description`. Prices in rupees. Each size of a product is its own row. All brands and products are fictional. |
| `search.py` | A simple local search: exact filters plus keyword ranking. No synonyms, no meaning. |
| `dev.jsonl` | 300 requests with the answers, for your own development and testing. Not used to score submissions. |
| `evaluate.py` | The scoring script, and a baseline agent that waits for the whole request. |

### `dev.jsonl`

One request per line:

```json
{"id": "dev-0042",
 "text": "I'm looking for black Pacevo running shoes size nine under four thousand please",
 "words": ["I'm", "looking", "for", "black", "Pacevo", "running", "shoes", "size", "nine", "under", "four", "thousand", "please"],
 "filters": {"category": "running shoes", "colour": "black", "size": "9", "brand": "Pacevo", "max_price": 4000},
 "target": "P0063",
 "earliest": 9,
 "tags": []}
```

- `filters` are what the whole request asks for; `null` means not mentioned.
- `target` is the one product that fits them.
- `earliest` is the word after which what has been said already pins down the target for good
  (for analysis; your agent never sees it).
- `tags`: `correction` ("black, no wait, white", or "…sorry, I meant size ten" at the end),
  `late_constraint` (a filter that arrives after the request sounded finished),
  `code_mixed` (Hindi–English). Untagged requests are plain.

Submissions are scored on a hidden test set of ~300 different requests: the same kinds of requests
over the same catalogue, with some wording you will not find in `dev.jsonl`.

## Your agent

A class named `Agent` (or pass `--agent file.py:ClassName`):

```python
class Agent:
    def __init__(self, tools):
        self.tools = tools              # see "Searches" below

    def start(self, request_id):
        """A new request begins."""

    def observe(self, word):
        """One more word. Return None to wait, or a dict:
             {"commit": "P0063"}                  show the shopper this product now
             {"filters": {...}, "confidence": 0.8} your current reading (optional, for analysis)
        Keys can be combined."""

    def finish(self):
        """The request is complete. Return your final product_id (None keeps your last commit)."""
```

- **Committing** means the product is shown to the shopper at that moment. You can commit again
  to a different product later, but every commit to a product that is not the target counts as
  a wrong commit.
- **`finish()`** is the check against the full request: your final answer is what accuracy is
  scored on.
- Your agent sees only the words so far. It must not read `dev.jsonl` or any test data at run time.

### Searches

Every search counts, wherever it runs:

- `tools.search(query="", filters=None, k=10)` runs `search.search` over the local catalogue and
  counts one search.
- `tools.record_search(n=1)` counts searches you ran elsewhere, for example with Rezolve Labs
  product search. Call it once per call you make.

Treat the catalogue as a remote store: read `catalogue.csv` as much as you like to build
vocabularies or train models, but at run time look products up through searches you count.
The jury reads the code.

## Scoring

Per request, then averaged and multiplied by 100:

```
score = (0.4 + 0.6 × earliness  if the final answer is right, else 0)
        − 1.0 × wrong commits
        − 0.02 × wasted searches (at most 10 counted)

earliness      = words still to come when you first committed the target ÷ words in the request
                 (0 if you never committed it, made a wrong commit, or got the final answer wrong)
wasted searches = searches − 1
```

`evaluate.py` also prints accuracy against the baseline (**it must not fall below the
baseline's**), wrong commits, earliness against the best possible, searches, latency per word,
a breakdown by tag, and, if your agent reports them, how well its filters match the gold ones at
the last word. `--log results.jsonl` writes one line per request.

The baseline scores **20.0** on `dev.jsonl` (accuracy 0.527, no early commits). Entries below 60%
of the reference baseline on the hidden set are not shortlisted. The weights above are proposals
and may be tuned before the competition opens; the script is the source of truth.

## Rezolve Labs

Your solution must use at least one Rezolve Labs capability; list them in your architecture
note. Each team gets a credit coupon for its Labs account. Useful here:

- **Managed knowledge retrieval** holds your catalogue: upload `catalogue.csv` as it is.
- **Semantic product search** searches it by meaning, with filters on any column. One credit
  per search. It can serve the early searches on a partial request, and understands words the
  local search does not.
- **Conversational product finder**: the same search as a tool an agent calls mid-conversation.
- **Live transcription** (stretch goal): stream audio over a WebSocket for a voice demo.

Loading the catalogue takes three calls (send your key in `X-API-KEY`):

```bash
API=https://api.rezolvelabs.com/api/v1

# 1. create a knowledge base; keep data.id
curl -s -X POST $API/developer-platform/knowledge-bases -H "X-API-KEY: $KEY" \
  -H 'Content-Type: application/json' -d '{"name": "PS1 catalogue"}'

# 2. upload the catalogue; keep data.id (the document)
curl -s -X POST $API/developer-platform/knowledge-bases/$KB/documents -H "X-API-KEY: $KEY" \
  -F file=@catalogue.csv

# 3. poll until status is "ready" (about 10 seconds); availableFilters lists the columns
curl -s $API/developer-platform/knowledge-bases/$KB/documents/$DOC -H "X-API-KEY: $KEY"
```

Then search:

```bash
curl -s -X POST $API/product-discovery/search -H "X-API-KEY: $KEY" -H 'Content-Type: application/json' \
  -d '{"knowledgeBaseId": "'$KB'", "query": "black running shoes",
       "filters": {"category": "running shoes", "colour": "black", "size": "9", "price_lte": 4000},
       "limit": 5}'
```

Each result's `id` is the catalogue's `product_id`. A plain filter value means equals; ranges use
`_gte`, `_lte`, `_gt`, `_lt` (`price_lte`). `hitCount` is the number of results returned, not
the number that matched: use `hasMore` to tell one match from several. Remember
`tools.record_search()` for every call.

## Submitting

Per the competition rules: an abstract (max 500 words), a 3-minute demo video, your code
repository with its outputs on `dev.jsonl` (`--log`), and the list of Rezolve Labs capabilities
you used.
