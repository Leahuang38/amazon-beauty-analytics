# Amazon Beauty & Personal Care Review Analytics

An exploratory portfolio project using Amazon Reviews 2023's `All_Beauty` category to examine product ratings and the language customers use in reviews. It combines product-level rating summaries with pooled and product-specific comparisons of low- and high-rated review text.

> Review patterns are descriptive. They do not establish product quality, sales, or what caused a rating.

## Research Questions

- How do one- and five-star review counts and shares vary among the most-reviewed products?
- Which words and short phrases appear more often in low-rated (1–2 star) versus high-rated (4–5 star) reviews?
- Do those language patterns differ within selected high-review products?

## Selected Findings

- Among the ten most-reviewed listings, the Salux wash cloth has an 82.52% five-star share and 4.33% one-star share. The Curly Co. diffuser has a 44.05% five-star share and an 18.22% one-star share.
- Across the category, `waste` and `disappointed` appear more often in low-rated reviews; `great` and `love` appear more often in high-rated reviews.
- Within the Curly Co. diffuser reviews, `not fit` appears in 14.94% of low-rated reviews versus 1.97% of high-rated reviews. `Kept collapsing` appears in 3.80% versus 0.13%.

These are exploratory word and phrase frequency differences, not causal findings. Individual terms should be interpreted in their original sentence context.

## Visual Results

### Product Ratings

![One- and five-star review counts for the ten most-reviewed products](reports/01_product_star_counts.png)

[Product rating data](reports/01_product_star_counts.csv)

### Review Language Across the Category

![Common words in low- and high-rated reviews](reports/02_review_terms_by_rating.png)

[Pooled term comparison data](reports/02_review_terms_by_rating.csv)

### Review Language Within Selected Products

![Phrase comparison within five selected products](reports/03_selected_product_phrase_comparison.png)

[Product phrase comparison data](reports/03_selected_product_phrase_comparison.csv)

For methods, data-quality results, full findings, and limitations, see the [detailed analysis report](reports/README.md).

## Data

The project uses 701,528 review records and 112,590 product metadata records from Amazon Reviews 2023's `All_Beauty` category, published by the McAuley Lab at UC San Diego. Review dates span May 1996 through September 2023.

- [Amazon Reviews 2023 project](https://amazon-reviews-2023.github.io/)
- [McAuley Lab dataset page](https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/)
- [All_Beauty review file](https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/All_Beauty.jsonl.gz)
- [All_Beauty product metadata](https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_All_Beauty.jsonl.gz)

Raw data is excluded from Git. Download both files from the project root:

```bash
mkdir -p data/raw
curl -L "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/All_Beauty.jsonl.gz" -o data/raw/All_Beauty.jsonl.gz
curl -L "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_All_Beauty.jsonl.gz" -o data/raw/meta_All_Beauty.jsonl.gz
```

## Reproduce

Python 3.13 was used. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the analyses with the project interpreter:

```bash
./.venv/bin/python scripts/01_inspect_data.py
./.venv/bin/python scripts/02_check_data_quality.py
./.venv/bin/python scripts/02_product_star_counts.py
./.venv/bin/python scripts/03_review_text_comparison.py
./.venv/bin/python scripts/04_product_review_comparison.py
```

## Data Quality

- Ratings are non-missing integers from 1 to 5; all distinct review product IDs match product metadata.
- 720 review bodies are blank. They remain eligible for rating counts and are omitted only from text analysis.
- 7,276 rows share a core set of review fields and are flagged as possible duplicates; they were not automatically removed.
- Price is missing for 84.28% of product records, so price analysis is out of scope.

[Download the data-quality report](reports/00_data_quality.csv)

## Limitations

- Review volume is not orders, sales, revenue, or inventory. Reviews reflect customers who chose to leave feedback.
- Some listings in the `All_Beauty` category appear outside typical beauty and personal care. The five product examples were selected by title relevance and are illustrative, not representative of the full category.
- Text analysis uses simple English tokenization, stop-word removal, and review-level word or adjacent-phrase frequencies. It is not a topic model, sentiment model, or causal analysis.
- Three-star reviews are omitted from low/high text comparisons; rating-group sizes differ.
- This is historical marketplace feedback, not a live view of Amazon rankings, reviews, or prices.

## Project Structure

```text
amazon-beauty-analytics/
├── data/raw/       # Downloaded source files; excluded from Git
├── reports/        # Charts, CSV outputs, and detailed analysis
├── scripts/        # Data checks and analysis scripts
├── sql/            # DuckDB SQL examples
├── requirements.txt
└── README.md
```

# Amazon Beauty & Personal Care Analytics

An independent portfolio project studying customer feedback and product positioning across Amazon beauty and personal-care products. It uses the Amazon Reviews 2023 `All_Beauty` category from McAuley Lab. The review file has about 701,500 reviews; product metadata has about 112,600 products. The compressed source files total about 136 MB.

## Why this project

Beauty and personal care is a consumer-goods category, and the products include everyday-use goods as well as premium brands. This dataset supports analysis of ratings, review themes, review helpfulness, brand/product comparisons, and price where the listing has a price. It does **not** contain actual orders, units sold, revenue, or inventory, so do not present review counts as sales.

## Source data

- Project website and dataset description: [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/)
- Original research dataset: [McAuley Lab, UC San Diego](https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/)
- [All_Beauty reviews JSONL.GZ](https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/All_Beauty.jsonl.gz)
- [All_Beauty product metadata JSONL.GZ](https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_All_Beauty.jsonl.gz)
- GitHub learning/reference project: [Amazon Reviews 2023 analytics workflow](https://github.com/ozukun/amazon-reviews-2023). Use it to learn project organization; write and explain your own analysis for a portfolio.

The dataset spans reviews collected from May 1996 through September 2023. Treat it as historical marketplace feedback, not a live view of today's product rankings or prices.

## Set up on this Mac

Python 3.13 from Miniforge is installed at `~/miniforge3/bin/python3`. DuckDB runs inside Python as a local embedded database; no separate database server is needed.

```bash
cd "/Users/azalea/Desktop/TAOBao project/amazon-beauty-analytics"
~/miniforge3/bin/python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

In VS Code, select `.venv/bin/python` using **Python: Select Interpreter**.

## Check the data

With the environment active:

```bash
python scripts/01_inspect_data.py
```

The script reads the compressed JSON Lines files directly, prints row counts and fields, and previews example review and product records.

## Questions to explore

1. Which brands and products receive consistently high or low ratings?
2. What topics appear more often in low-star versus high-star reviews?
3. Do review volume and average rating tell the same story?
4. Where product price is available, how do ratings and review themes vary across price bands?
5. Which review themes receive the most helpful votes?

## Structure

```text
amazon-beauty-analytics/
├── data/raw/          # Source files; ignored by Git
├── data/processed/    # Derived files; ignored by Git
├── reports/           # Figures and written findings
├── scripts/           # Python analysis scripts
├── sql/               # DuckDB SQL queries
├── requirements.txt
└── README.md
```

For a strong portfolio result, document how you clean and join reviews to products, distinguish review volume from sales, account for products with very few ratings, and support each business recommendation with evidence. The reviews contain user-written text; avoid publishing user identifiers or unnecessary personal details.
├── data/raw/          # Downloaded source data; excluded from Git
