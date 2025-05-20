# -*- coding: utf-8 -*-
"""
Created on Tue May 20 12:44:53 2025

@author: tommy
"""

import faiss
import pickle
from sentence_transformers import SentenceTransformer

class AnswerRetriever:
    def __init__(self, index_path: str, metadata_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model_name = model_name
        self._index = None
        self._metadata = None
        self._embedder = None

    @property
    def index(self):
        if self._index is None:
            self._index = faiss.read_index(self.index_path)
        return self._index

    @property
    def metadata(self):
        if self._metadata is None:
            with open(self.metadata_path, "rb") as f:
                self._metadata = pickle.load(f)
        return self._metadata

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    def get_nearest_neighbors(self, query: str, n: int = 3):
        query_vec = self.embedder.encode([query], convert_to_numpy=True)
        D, I = self.index.search(query_vec, k=n)
        return [self.metadata[i] for i in I[0]]
