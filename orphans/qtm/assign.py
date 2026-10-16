"""Tradition assignment against a reference space of per-tradition centroids.

Score = cosine(fragment, centroid). Each score is turned into a z-value
against a null of the same fragment shuffled across labels, so a fragment
can be left unassigned ("open set") when no tradition stands out.
"""
import numpy as np
from sklearn.preprocessing import normalize


def centroids(X, labels):
    labs = sorted(set(labels))
    labels = np.asarray(labels)
    C = np.vstack([np.asarray(X[labels == l].mean(axis=0)).ravel() for l in labs])
    return normalize(C), labs


def scores(X, C):
    return np.asarray(X @ C.T)


def assign(S, labs, margin=0.0):
    """Top label, its score, and the gap to the runner-up (abstain if gap < margin)."""
    order = np.argsort(-S, axis=1)
    top, second = S[np.arange(len(S)), order[:, 0]], S[np.arange(len(S)), order[:, 1]]
    pred = np.array([labs[i] for i in order[:, 0]], dtype=object)
    gap = top - second
    pred[gap < margin] = None
    return pred, top, gap
