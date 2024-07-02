import hashlib
import json
from typing import List, Optional
from upstash_vector import Index
from langchain_core.outputs.generation import Generation


class SemanticCache:
    def __init__(self, url, token, min_proximity: float = 0.9):
        self.min_proximity = min_proximity
        self.index = Index(url=url, token=token)

    # searches the cache for the key and returns the value if it exists
    def get(self, key: str):
        response = self.query_key(key)
        if response is None or response.score <= self.min_proximity:
            return None
        return response.metadata["data"]

    # langchain specific function
    # converts the json string to generations and returns
    def lookup(self, prompt: str, llm_string: Optional[str] = None):
        result = self.get(prompt)
        return self._loads_generations(result) if result else None

    # another langchain specific function
    # converts the generations to a json string and stores it in the cache
    def update(
        self,
        prompt: str,
        llm_string: Optional[str] = None,
        result: Optional[str] = None,
    ):
        self.set(prompt, self._dumps_generations(result))

    # queries the cache for the key
    def query_key(self, key: str):
        response = self.index.query(data=key, top_k=1, include_metadata=True)
        return response[0] if response else None

    # sets the key and value in the cache
    def set(self, key: Optional[str | List[str]], data: Optional[str | List[str]]):
        if (type(key) is list) and (type(data) is list):
            for i in range(len(key)):
                currrent_key = key[i]
                self.index.upsert(
                    [(self._hash_key(currrent_key), currrent_key, {"data": data[i]})]
                )
        else:
            self.index.upsert([(self._hash_key(key), key, {"data": data})])

    def delete(self, key: str):
        self.index.delete([self._hash_key(key)])

    def bulk_delete(self, keys: List[str]):
        for key in keys:
            self.delete(key)

    def flush(self):
        self.index.reset()

    # helper functions
    def _is_2d_list(self, lst):
        return isinstance(lst, list) and all(
            isinstance(sublist, list) for sublist in lst
        )

    # converts the generations to a json string
    def _dumps_generations(self, generations):
        def generation_to_dict(generation):
            if isinstance(generation, Generation):
                return {
                    "text": generation.text,
                    "generation_info": generation.generation_info,
                }
            else:
                raise TypeError(
                    f"Object of type {generation.__class__.__name__} is not JSON serializable"
                )

        return json.dumps([generation_to_dict(g) for g in generations])

    # converts the json string to generations
    def _loads_generations(self, json_str):
        def dict_to_generation(d):
            if isinstance(d, dict):
                return Generation(text=d["text"], generation_info=d["generation_info"])
            else:
                raise TypeError(
                    f"Object of type {d.__class__.__name__} is not a valid Generation dict"
                )

        return [dict_to_generation(d) for d in json.loads(json_str)]

    # hashes the key to generate id
    def _hash_key(self, key):
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
