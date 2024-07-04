from time import sleep
import unittest
from upstash_semantic_cache.semantic_caching import SemanticCache
from dotenv import load_dotenv
import os

load_dotenv()

UPSTASH_VECTOR_REST_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
UPSTASH_VECTOR_REST_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

# Initialize Upstash Vector Index


class TestSemanticCache(unittest.TestCase):
    key1 = "key1"
    key2 = "key2"
    data1 = "value1"
    data2 = "value2"

    def setUp(self):
        # Initialize the SemanticCache instance
        self.cache = SemanticCache(
            UPSTASH_VECTOR_REST_URL, UPSTASH_VECTOR_REST_TOKEN, min_proximity=0.7
        )
        self.refresh()

    def test_get_existing_key(self):
        # Set up a key-value pair in the cache

        self.cache.set(self.key1, self.data1)
        sleep(1)
        # Retrieve the value using the key
        result = self.cache.get(self.key1)
        sleep(1)
        # Assert that the retrieved value is correct
        self.assertEqual(result, self.data1)
        self.refresh()

    def test_get_nonexistent_key(self):
        # Retrieve a non-existent key
        result = self.cache.get("nonexistent_key")

        # Assert that the result is None
        self.assertIsNone(result)
        self.refresh()

    def test_set_multiple_key_values(self):
        # Set up multiple key-value pairs in the cache
        keys = [self.key1, self.key2]
        data = [self.data1, self.data2]
        self.cache.set(keys, data)
        sleep(1)
        # Retrieve the values using the keys
        result1 = self.cache.get(keys[0])
        sleep(1)
        result2 = self.cache.get(keys[1])
        sleep(1)
        # Assert that the retrieved values are correct
        self.assertEqual(result1, data[0])
        self.assertEqual(result2, data[1])
        self.refresh()

    def test_delete_existing_key(self):
        self.cache.set(self.key1, self.data1)
        sleep(1)
        # Delete the key
        self.cache.delete(self.key1)
        sleep(1)
        # Retrieve the value using the key
        result = self.cache.get(self.key1)
        sleep(1)
        # Assert that the result is None
        self.assertIsNone(result)
        self.refresh()

    def test_delete_nonexistent_key(self):
        # Set up a key-value pair in the cache
        key = self.key1
        data = self.data1
        self.cache.set(key, data)
        sleep(1)
        # Delete a non-existent key
        result = self.cache.delete("nonexistent_key")
        sleep(1)
        # Assert that the result is False
        self.assertFalse(result)
        self.refresh()

    def test_bulk_delete(self):
        # Set up multiple key-value pairs in the cache
        keys = [self.key1, self.key2, "key3"]
        data = [self.data1, self.data2, "value3"]
        self.cache.set(keys, data)
        sleep(1)
        # Delete multiple keys
        self.cache.delete(keys)
        sleep(1)
        # Retrieve the values using the keys
        result1 = self.cache.get(keys[0])
        sleep(1)
        result2 = self.cache.get(keys[1])
        sleep(1)
        result3 = self.cache.get(keys[2])
        sleep(1)

        # Assert that the results are None
        self.assertIsNone(result1)
        self.assertIsNone(result2)
        self.assertIsNone(result3)
        self.refresh()

    def test_flush(self):
        # Set up a key-value pair in the cache
        key = self.key1
        data = self.data1
        self.cache.set(key, data)
        # Flush the cache
        self.cache.flush()
        # Retrieve the value using the key
        result = self.cache.get(key)
        # Assert that the result is None
        self.assertIsNone(result)
        self.refresh()

    def refresh(self):
        self.cache.flush()
        sleep(1)


if __name__ == "__main__":
    unittest.main()
