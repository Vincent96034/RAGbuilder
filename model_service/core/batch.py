import time
import logging

from openai import RateLimitError
from langchain_core.runnables import Runnable


def batch_invoke_with_retry(
        chain: Runnable,
        input_list: list,
        max_retries: int = 5,
        user_tier: int = 1
) -> list:
    """Invoke a chain with a list of inputs in batches, with retries on rate limit errors.

    Args:
        chain: The chain to invoke.
        input_list: The list of inputs to process.
        user_tier: The user's OpenAI API tier.
    """

    results = []
    max_retries = 5
    delay_increment = 60

    # Optimized batch size calculation
    batch_size = min(30 if user_tier < 4 else 80, len(input_list))
    logging.debug(f"Batch Size: {batch_size}")

    for i in range(0, len(input_list), batch_size):
        batch = input_list[i: i + batch_size]

        retries = 0
        while retries <= max_retries:
            try:
                result = chain.batch(batch)
                results.append(result)
                time.sleep(2)
                break  # Exit the retry loop once successful

            except RateLimitError as rate_limit_error:
                delay = (retries + 1) * delay_increment
                logging.warning(f"{rate_limit_error}. Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1

                if retries > max_retries:
                    logging.error(
                        f"Max retries reached for batch starting at index {i}. Skipping to next batch.")
                    break

    return results
