"""Feature spaces: word tf-idf and orthographic sign n-grams (within word, n=1..3)."""
from sklearn.feature_extraction.text import TfidfVectorizer

LOGOGRAM = lambda t: t.isupper()  # Sumero-/Akkadograms are upper-case in TLHdig transliteration


def word_tokens(words, drop_logograms=False):
    return [w for w in words if not (drop_logograms and any(c.isupper() for c in w[:1]))]


def sign_ngrams(sign_lists, n=(1, 3), drop_logograms=False):
    out = []
    for sg in sign_lists:
        if drop_logograms:
            sg = [s for s in sg if not LOGOGRAM(s)]
        for k in range(n[0], n[1] + 1):
            out += ["·".join(sg[i:i + k]) for i in range(len(sg) - k + 1)]
    return out


def vectorizer(min_df=2, sublinear=True):
    return TfidfVectorizer(analyzer=lambda toks: toks, min_df=min_df,
                           sublinear_tf=sublinear, norm="l2")


def tokens(doc, space="words", **kw):
    if space == "words":
        return word_tokens(doc["words"], **kw)
    if space == "signs":
        return sign_ngrams(doc["signs"], **kw)
    if space == "both":
        return word_tokens(doc["words"], **kw) + ["§" + t for t in sign_ngrams(doc["signs"], **kw)]
    raise ValueError(space)
