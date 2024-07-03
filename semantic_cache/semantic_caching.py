import hashlib
import json
from typing import List, Optional, Union
from upstash_vector import Index
from langchain_core.outputs.generation import Generation


class SemanticCache:
    """
    A class to represent a semantic cache using Upstash Vector Database.

    Attributes:
        min_proximity (float): The minimum proximity score to consider a cache hit.
        index (Index): The Upstash Vector index object.
    """

    def __init__(self, url: str, token: str, min_proximity: float = 0.9) -> None:
        """
        Initializes the SemanticCache with the given URL and token.

        Args:
            url (str): The URL of the Upstash Vector database.
            token (str): The token for accessing the Upstash Vector database.
            min_proximity (float): The minimum proximity score to consider a cache hit.
        """
        self.min_proximity = min_proximity
        self.index = Index(url=url, token=token)

    def get(self, key: str) -> Optional[str]:
        """
        Searches the cache for the key and returns the value if it exists.

        Args:
            key (str): The key to search in the cache.

        Returns:
            Optional[str]: The value associated with the key
            if it exists and meets the proximity score; otherwise, None.
        """
        response = self._query_key(key)
        if response is None or response.score <= self.min_proximity:
            return None
        return response.metadata["data"]

    def lookup(
        self, prompt: str, llm_string: Optional[str] = None
    ) -> Optional[List[Generation]]:
        """
        Converts the JSON string to generations and returns them.
        It is called by Langchain to check if the generations are in the cache.

        Args:
            prompt (str): The prompt to lookup in the cache.
            llm_string (Optional[str]): Optional string for LLM context.

        Returns:
            Optional[List[Generation]]:
            If response is found in the cache; otherwise, None.
        """
        result = self.get(prompt)
        return self._loads_generations(result) if result else None

    def update(
        self,
        prompt: str,
        llm_string: Optional[str] = None,
        result: Optional[str] = None,
    ) -> None:
        """
        Converts the generations to a JSON string and stores it in the cache.
        It is called by Langchain to upload the generations to the cache.

        Args:
            prompt (str): The prompt to update in the cache.
            llm_string (Optional[str]): Optional string for LLM context.
            result (Optional[str]): The result to store in the cache.
        """
        self.set(prompt, self._dumps_generations(result))

    def set(self, key: Union[str, List[str]], data: Union[str, List[str]]) -> None:
        """
        Sets the key and value in the cache.

        Args:
            key (Union[str, List[str]]): The key(s) to set in the cache.
            data (Union[str, List[str]]): The value(s) to associate with the key(s).
        """
        if isinstance(key, list) and isinstance(data, list):
            for i in range(len(key)):
                currrent_key = key[i]
                self.index.upsert(
                    [(self._hash_key(currrent_key), currrent_key, {"data": data[i]})]
                )
        else:
            self.index.upsert([(self._hash_key(key), key, {"data": data})])

    def delete(self, key: str) -> None:
        """
        Deletes the key from the cache.

        Args:
            key (str): The key to delete from the cache.
        """
        self.index.delete([self._hash_key(key)])

    def bulk_delete(self, keys: List[str]) -> None:
        """
        Deletes multiple keys from the cache.

        Args:
            keys (List[str]): The keys to delete from the cache.
        """
        for key in keys:
            self.delete(key)

    def flush(self) -> None:
        """
        Resets the cache, removing all keys and values.
        """
        self.index.reset()

    def _query_key(self, key: str):
        """
        Queries the cache for the key.

        Args:
            key (str): The key to query in the cache.

        Returns:
            The response from the cache query.
        """
        response = self.index.query(data=key, top_k=1, include_metadata=True)
        return response[0] if response else None

    def _is_2d_list(self, lst) -> bool:
        """
        Checks if the given list is a 2D list.

        Args:
            lst: The list to check.

        Returns:
            bool: True if the list is a 2D list; otherwise, False.
        """
        return isinstance(lst, list) and all(
            isinstance(sublist, list) for sublist in lst
        )

    def _dumps_generations(self, generations):
        """
        Converts the generations to a JSON string.
        """

        def generation_to_dict(generation):
            if isinstance(generation, Generation):
                return {
                    "text": generation.text,
                    "generation_info": generation.generation_info,
                }
            else:
                raise TypeError(
                    f"Object of type {generation.__class__.__name__}"
                    + "is not JSON serializable"
                )

        return json.dumps([generation_to_dict(g) for g in generations])

    def _loads_generations(self, json_str):
        """
        Converts the JSON string to generations.
        """

        def dict_to_generation(d: dict) -> Generation:
            if isinstance(d, dict):
                return Generation(text=d["text"], generation_info=d["generation_info"])
            else:
                raise TypeError(
                    f"Object of type {d.__class__.__name__}"
                    + "is not a valid Generation dict"
                )

        return [dict_to_generation(d) for d in json.loads(json_str)]

    def _hash_key(self, key):
        """
        Hashes the key to generate an ID.
        """
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
