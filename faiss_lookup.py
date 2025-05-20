# -*- coding: utf-8 -*-
"""
Created on Tue May 20 12:44:53 2025

@author: tommy
"""

import faiss
import pickle
import requests
import numpy as np
from io import BytesIO
from sentence_transformers import SentenceTransformer
import streamlit as st
import tempfile

class AnswerRetriever:
    def __init__(self, faiss_url: str, metadata_url: str, model_name: str = "all-MiniLM-L6-v2"):
        self.faiss_url = faiss_url
        self.metadata_url = metadata_url
        self.model_name = model_name
        self._index = None
        self._metadata = None
        self._embedder = None

    @property
    def index(self):
        if self._index is None:
            response = requests.get(self.faiss_url)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(response.content)
                tmp.flush()
                self._index = faiss.read_index(tmp.name)
        return self._index

    @property
    def metadata(self):
        if self._metadata is None:
            response = requests.get(self.metadata_url)
            response.raise_for_status()
            self._metadata = pickle.load(BytesIO(response.content))
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
