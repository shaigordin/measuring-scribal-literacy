"""Tradition assignment against a reference space of per-tradition centroids.

Score = cosine(fragment, centroid of a tradition). Leave-one-out scores are
computed in closed form (each text is removed from its own class sum), so
permutation baselines over thousands of texts stay cheap.
"""
import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize


def class_sums(X, y, labs):
    Y = sparse.csr_matrix((np.ones(len(y)), (np.searchsorted(labs, y), np.arange(len(y)))),
                          shape=(len(labs), len(y)))
    return np.asarray((Y @ X).todense()) if sparse.issparse(X) else Y @ X


def centroids(X, y):
    labs = np.array(sorted(set(y)))
    return normalize(class_sums(X, np.asarray(y), labs)), labs


def scores(X, C):
    S = X @ C.T
    return np.asarray(S.todense()) if sparse.issparse(S) else np.asarray(S)


def loo_scores(X, y):
    """Cosine of each text to every class centroid, with the text left out of its own class."""
    y = np.asarray(y)
    labs = np.array(sorted(set(y)))
    sums = class_sums(X, y, labs)                       # (k, d)
    dot = scores(X, sums)                               # x_i . s_c
    sq = (sums ** 2).sum(1)                             # |s_c|^2
    xx = np.asarray(X.multiply(X).sum(1)).ravel() if sparse.issparse(X) else (X ** 2).sum(1)
    own = np.searchsorted(labs, y)
    rows = np.arange(len(y))
    num, den2 = dot.copy(), np.tile(sq, (len(y), 1))
    num[rows, own] -= xx
    den2[rows, own] += -2 * dot[rows, own] + xx
    S = num / np.sqrt(np.maximum(den2, 1e-12))
    counts = np.bincount(own, minlength=len(labs))
    S[rows[counts[own] == 1], own[counts[own] == 1]] = -np.inf  # singleton class: no centroid left
    return S, labs


def assign(S, labs, margin=0.0):
    """Top label, its score, and the gap to the runner-up (None if gap < margin)."""
    order = np.argsort(-S, axis=1)
    r = np.arange(len(S))
    top, second = S[r, order[:, 0]], S[r, order[:, 1]]
    pred = np.array([labs[i] for i in order[:, 0]], dtype=object)
    gap = top - second
    pred[gap < margin] = None
    return pred, top, gap
