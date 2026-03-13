import asyncio
import random
from functools import wraps
from typing import Callable, TypeVar, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

from utils.errors import FloodWaitError, RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 5,
        min_wait: float = 1.0,
        max_wait: float = 60.0,
        jitter: float = 1.0
    ):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.jitter = jitter


async def exponential_backoff_retry(
    func: Callable[..., T],
    *args,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    **kwargs
) -> T:
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except FloodWaitError as e:
            last_exception = e
            retry_after = e.details.get("retry_after", base_delay * (2 ** attempt))
            retry_after = min(retry_after, max_delay)
            jitter = random.uniform(0, 1)
            wait_time = retry_after + jitter
            
            logger.warning(f"FloodWait: retrying after {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(wait_time)
            
        except RateLimitError as e:
            last_exception = e
            retry_after = e.details.get("retry_after", base_delay * (2 ** attempt))
            jitter = random.uniform(0, 1)
            wait_time = retry_after + jitter
            
            logger.warning(f"RateLimit: retrying after {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            error_str = str(e).lower()
            if "flood wait" in error_str or "too many requests" in error_str:
                last_exception = e
                import re
                match = re.search(r'(\d+)', str(e))
                retry_after = int(match.group(1)) if match else base_delay * (2 ** attempt)
                retry_after = min(retry_after, max_delay)
                jitter = random.uniform(0, 1)
                wait_time = retry_after + jitter
                
                logger.warning(f"Flood detected: retrying after {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    if last_exception:
        raise last_exception
    raise Exception("Max retries exceeded")


def with_retry(config: RetryConfig = None):
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await exponential_backoff_retry(
                func,
                *args,
                max_attempts=config.max_attempts,
                base_delay=config.min_wait,
                max_delay=config.max_wait,
                **kwargs
            )
        return wrapper
    return decorator


class RateLimiter:
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        now = asyncio.get_event_loop().time()
        self.requests = [r for r in self.requests if now - r < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        self.requests.append(now)
    
    def reset(self):
        self.requests = []
