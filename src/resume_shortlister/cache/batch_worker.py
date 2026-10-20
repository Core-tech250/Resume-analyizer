import time
from typing import List, Callable, Optional, Dict, Any

class BatchProcessor:
    """
    Handles chunked batch processing of hundreds of resumes with progress tracking.
    """
    def __init__(self, chunk_size: int = 50):
        self.chunk_size = chunk_size

    def process_resumes_in_batches(
        self,
        resume_items: List[Any],
        process_fn: Callable[[Any], Any],
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> List[Any]:
        results = []
        total = len(resume_items)
        if total == 0:
            return results

        t_start = time.perf_counter()

        for idx, item in enumerate(resume_items):
            res = process_fn(item)
            results.append(res)

            if progress_callback and (idx % 10 == 0 or idx == total - 1):
                elapsed = time.perf_counter() - t_start
                progress_callback(idx + 1, total, elapsed)

        return results

batch_processor = BatchProcessor(chunk_size=50)
