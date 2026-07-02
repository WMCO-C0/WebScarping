"""
Módulo de resiliencia: Retry, backoff, circuit breaker, rate limiting.
"""
import time
import random
import logging
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Limita la tasa de requests por dominio."""
    
    def __init__(self):
        self._requests = defaultdict(list)
        self._delays = {}
    
    def set_delay(self, domain, delay):
        """Establece delay mínimo entre requests para un dominio."""
        self._delays[domain] = delay
    
    def wait(self, domain):
        """Espera si es necesario antes de hacer un request."""
        delay = self._delays.get(domain, 0.5)
        now = datetime.now()
        
        # Limpiar requests antiguos
        cutoff = now - timedelta(seconds=delay * 2)
        self._requests[domain] = [
            t for t in self._requests[domain] if t > cutoff
        ]
        
        # Si hay requests recientes, esperar
        if self._requests[domain]:
            elapsed = (now - self._requests[domain][-1]).total_seconds()
            if elapsed < delay:
                wait_time = delay - elapsed + random.uniform(0.1, 0.3)
                logger.debug(f"Rate limit: esperando {wait_time:.2f}s para {domain}")
                time.sleep(wait_time)
        
        self._requests[domain].append(datetime.now())


class CircuitBreaker:
    """Circuit breaker para evitar golpear un sitio caído."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self._failures = defaultdict(int)
        self._last_failure = {}
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._open = defaultdict(bool)
    
    def record_failure(self, domain):
        """Registra un fallo para un dominio."""
        self._failures[domain] += 1
        self._last_failure[domain] = datetime.now()
        
        if self._failures[domain] >= self._failure_threshold:
            self._open[domain] = True
            logger.warning(f"Circuit breaker ABIERTO para {domain}")
    
    def record_success(self, domain):
        """Registra un éxito (resetea contador)."""
        self._failures[domain] = 0
        self._open[domain] = False
    
    def is_open(self, domain):
        """Verifica si el circuit breaker está abierto."""
        if not self._open[domain]:
            return False
        
        # Verificar si ya pasó el tiempo de recuperación
        if domain in self._last_failure:
            elapsed = (datetime.now() - self._last_failure[domain]).total_seconds()
            if elapsed > self._recovery_timeout:
                self._open[domain] = False
                self._failures[domain] = 0
                logger.info(f"Circuit breaker CERRADO para {domain} (recuperado)")
                return False
        
        return True


def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=30.0, 
                       exponential=True, jitter=True):
    """
    Decorador para retry con backoff exponencial.
    
    Args:
        max_retries: Número máximo de reintentos
        base_delay: Delay base en segundos
        max_delay: Delay máximo en segundos
        exponential: Si True, usa backoff exponencial
        jitter: Si True, agrega variación aleatoria
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    # Calcular delay
                    if exponential:
                        delay = base_delay * (2 ** attempt)
                    else:
                        delay = base_delay
                    
                    # Agregar jitter
                    if jitter:
                        delay = delay * random.uniform(0.5, 1.5)
                    
                    # Limitar delay máximo
                    delay = min(delay, max_delay)
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} para {func.__name__}: {e}. "
                        f"Esperando {delay:.2f}s..."
                    )
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class SmartDelay:
    """Delay adaptativo basado en respuesta del servidor."""
    
    def __init__(self, initial_delay=0.5, min_delay=0.1, max_delay=5.0):
        self._delays = defaultdict(lambda: initial_delay)
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._success_count = defaultdict(int)
        self._error_count = defaultdict(int)
    
    def update(self, domain, success, status_code=None):
        """Actualiza el delay basado en la respuesta."""
        if success:
            self._success_count[domain] += 1
            self._error_count[domain] = 0
            
            # Si hay muchos éxitos consecutivos, reducir delay
            if self._success_count[domain] >= 10:
                self._delays[domain] = max(
                    self._min_delay,
                    self._delays[domain] * 0.9
                )
        else:
            self._error_count[domain] += 1
            self._success_count[domain] = 0
            
            # Si hay errores, aumentar delay
            if status_code == 429:  # Rate limited
                self._delays[domain] = min(
                    self._max_delay,
                    self._delays[domain] * 2
                )
                logger.warning(f"Rate limited en {domain}, delay: {self._delays[domain]:.2f}s")
            elif status_code and status_code >= 500:  # Server error
                self._delays[domain] = min(
                    self._max_delay,
                    self._delays[domain] * 1.5
                )
            elif self._error_count[domain] >= 3:
                self._delays[domain] = min(
                    self._max_delay,
                    self._delays[domain] * 1.2
                )
    
    def get_delay(self, domain):
        """Obtiene el delay actual para un dominio."""
        return self._delays[domain]