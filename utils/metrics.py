import time
from functools import wraps

def track_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"⏱️  {func.__name__}: {duration:.2f}s")
        return result
    return wrapper
```

### 10. **Add requirements-dev.txt**
```
pytest==7.4.3
black==23.12.1
flake8==7.0.0
mypy==1.8.0
