import re


TOKEN_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more",
    "most", "my", "myself", "of", "off", "on", "once", "only", "or", "other", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    "s", "t", "d", "ll", "m", "re", "ve",
}


def review_terms(text: str, phrases_only: bool = False) -> set[str]:
    tokens = TOKEN_PATTERN.findall(text.lower())
    terms = set()

    if not phrases_only:
        terms.update(token for token in tokens if token not in STOPWORDS and len(token) > 1)

    terms.update(
        f"{left} {right}"
        for left, right in zip(tokens, tokens[1:])
        if left not in STOPWORDS
        and right not in STOPWORDS
        and len(left) > 1
        and len(right) > 1
    )
    return terms