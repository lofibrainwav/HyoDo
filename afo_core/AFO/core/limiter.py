from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared Limiter Instance for Phase 56
limiter = Limiter(key_func=get_remote_address)
