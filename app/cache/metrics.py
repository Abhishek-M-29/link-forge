from prometheus_client import Counter

cache_hits = Counter("linkforge_cache_hits_total", "Redirect cache hits")
cache_misses = Counter("linkforge_cache_misses_total", "Redirect cache misses")
