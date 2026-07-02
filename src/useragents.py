"""
Módulo de User-Agent rotation y headers dinámicos.
"""
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# User-Agents populares (actualizados periódicamente)
USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Chrome (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class UserAgentRotator:
    """Rotador de User-Agents con estrategias configurables."""
    
    def __init__(self, strategy="random"):
        """
        Args:
            strategy: "random", "round-robin", "single"
        """
        self._strategy = strategy
        self._index = 0
        self._custom_ua = None
        self._used_agents = {}
    
    def set_single(self, user_agent):
        """Establece un User-Agent fijo."""
        self._strategy = "single"
        self._custom_ua = user_agent
    
    def get(self):
        """Obtiene un User-Agent según la estrategia."""
        if self._strategy == "single" and self._custom_ua:
            return self._custom_ua
        
        if self._strategy == "round-robin":
            ua = USER_AGENTS[self._index % len(USER_AGENTS)]
            self._index += 1
            return ua
        
        # Random (default)
        ua = random.choice(USER_AGENTS)
        
        # Evitar repetir el mismo 3 veces seguidas
        recent = self._used_agents.get("recent", [])
        if len(recent) >= 3 and all(r == ua for r in recent):
            while ua in recent:
                ua = random.choice(USER_AGENTS)
        
        recent.append(ua)
        if len(recent) > 10:
            recent = recent[-10:]
        self._used_agents["recent"] = recent
        
        return ua


class DynamicHeaders:
    """Genera headers dinámicos que parecen más naturales."""
    
    # Headers base por navegador
    BASE_HEADERS = {
        "chrome": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
        "firefox": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
        "safari": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        },
    }
    
    def __init__(self):
        self._referrer_pools = {}
    
    def get_headers(self, user_agent, referrer=None):
        """Genera headers completos para un User-Agent."""
        # Detectar navegador
        ua_lower = user_agent.lower()
        if "chrome" in ua_lower and "edg" not in ua_lower:
            browser = "chrome"
        elif "firefox" in ua_lower:
            browser = "firefox"
        elif "safari" in ua_lower:
            browser = "safari"
        else:
            browser = "chrome"  # Default
        
        headers = self.BASE_HEADERS[browser].copy()
        headers["User-Agent"] = user_agent
        
        if referrer:
            headers["Referer"] = referrer
        
        return headers
    
    def add_referrer(self, domain, referrer):
        """Agrega un referrer válido para un dominio."""
        if domain not in self._referrer_pools:
            self._referrer_pools[domain] = []
        self._referrer_pools[domain].append(referrer)
    
    def get_referrer(self, domain):
        """Obtiene un referrer válido para un dominio."""
        referrers = self._referrer_pools.get(domain, [])
        if referrers:
            return random.choice(referrers)
        return None


class DelayGenerator:
    """Genera delays aleatorios para parecer más humano."""
    
    def __init__(self, min_delay=0.5, max_delay=2.0, burst_chance=0.1):
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._burst_chance = burst_chance
        self._last_request = {}
    
    def get_delay(self, domain):
        """Genera un delay aleatorio."""
        # Delay base
        delay = random.uniform(self._min_delay, self._max_delay)
        
        # Ocasionalmente hacer una pausa más larga (como un humano)
        if random.random() < self._burst_chance:
            delay += random.uniform(1.0, 3.0)
        
        # Si el último request fue rápido, pausar más
        if domain in self._last_request:
            elapsed = (datetime.now() - self._last_request[domain]).total_seconds()
            if elapsed < 0.5:
                delay += random.uniform(0.5, 1.0)
        
        self._last_request[domain] = datetime.now()
        
        return delay