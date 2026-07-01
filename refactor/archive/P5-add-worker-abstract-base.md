# P5 — Add Worker Abstract Base

**Source:** V-004, TD-004  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 6 | **Implementation Order:** 5
**Hard Prerequisites:** None
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

Worker classes (`ContentExtractor`, `EntityExtractor`, `LocationExtractor`, etc.) in `workers/` shared no common interface. Each exposed a different method signature (`extract_content`, `extract_entities`, etc.). The `run_worker()` function instantiated each class directly and retrieved the method as a bound callable by name — a fragile pattern that broke silently if a worker renamed its method.

## Resolution (2026-07)

- ✅ `workers/base.py` created with `BaseWorker` ABC
- ✅ All 6 worker classes now inherit from `BaseWorker`
- ✅ All implement `process(job: dict) -> dict` method
- ✅ Handler registration uses `worker.process` uniformly

## Implementation Evidence

```python
# workers/base.py
class BaseWorker(ABC):
    @abstractmethod
    def process(self, job: dict) -> dict:
        """Process a single job."""
        pass

# workers/__init__.py exports BaseWorker
from .base import BaseWorker
```

All extractors now inherit and implement:
- `ContentExtractor(BaseWorker)`
- `EntityExtractor(BaseWorker)`
- `EventExtractor(BaseWorker)`
- `LocationExtractor(BaseWorker)`
- `EmbeddingGenerator(BaseWorker)`
- `PhotoMetadataExtractor(BaseWorker)`

Handler registration (e.g., in `app_state.py:349-368`):
```python
self.job_processor.register_handler(
    'extract_text', 
    ContentExtractor(self.backend, library_root).process
)
```

## Definition of Done

- ✅ `BaseWorker` ABC exists with `@abstractmethod process(job)`.
- ✅ All extractors implement `process`.
- ✅ `run_worker` / handler registration calls `worker.process(job)` uniformly.
- ✅ All existing tests pass.
