import os
from time import sleep
import time
from dotenv import load_dotenv
from upstash_semantic_cache.semantic_caching import SemanticCache
from langchain.globals import set_llm_cache
from langchain_openai import OpenAI


def example1(llm):
    prompt1 = "Why is the Moon always showing the same side?"
    prompt2 = "How come we always see one face of the moon?"

    start_time = time.time()
    response1 = llm.invoke(prompt1)
    print(response1)
    end_time = time.time()
    print("Time difference 1:", end_time - start_time, "seconds")
    sleep(1)

    start_time = time.time()
    response2 = llm.invoke(prompt2)
    print(response2)
    end_time = time.time()
    time_difference = end_time - start_time
    print("Time difference 2:", time_difference, "seconds")


def main():
    # set environment variables
    load_dotenv()
    UPSTASH_VECTOR_REST_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
    UPSTASH_VECTOR_REST_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

    # create a cache object
    cache = SemanticCache(
        url=UPSTASH_VECTOR_REST_URL, token=UPSTASH_VECTOR_REST_TOKEN, min_proximity=0.7
    )
    cache.flush()
    sleep(1)

    llm = OpenAI(model_name="gpt-3.5-turbo-instruct", n=2, best_of=2)
    set_llm_cache(cache)
    example1(llm)


main()
