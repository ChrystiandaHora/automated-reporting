import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import redis

logger = logging.getLogger("model_rate_limiter")

# Modelos padrão configurados no sistema
DEFAULT_MODELS = [
    {
        "id": "gemini-2.5-flash-lite",
        "name": "Gemini 2.5 Flash Lite",
        "category": "Modelos de texto",
        "rpm_limit": 10,
        "tpm_limit": 750000,
        "rpd_limit": 20,
    },
    {
        "id": "gemini-3.1-flash-lite",
        "name": "Gemini 3.1 Flash Lite",
        "category": "Modelos de texto",
        "rpm_limit": 15,
        "tpm_limit": 250000,
        "rpd_limit": 500,
    },
    {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "category": "Modelos de texto",
        "rpm_limit": 5,
        "tpm_limit": 250000,
        "rpd_limit": 20,
    },
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash Lite",
        "category": "Modelos de texto",
        "rpm_limit": 15,
        "tpm_limit": 250000,
        "rpd_limit": 500,
    },
]


class ModelRateLimiter:
    """Gerenciador de métricas e limites de taxa de API por modelo.

    Utiliza Redis como backend primário e faz fallback gracioso em memória
    caso o servidor Redis não esteja acessível.
    """

    def __init__(self):
        self._models_config: Dict[str, Dict[str, Any]] = {
            m["id"]: dict(m) for m in DEFAULT_MODELS
        }
        self._redis_client: Optional[redis.Redis] = None
        # Fallback em memória caso o Redis esteja indisponível
        self._memory_rpm: Dict[str, Dict[int, int]] = {}
        self._memory_tpm: Dict[str, Dict[int, int]] = {}
        self._memory_rpd: Dict[str, Dict[str, int]] = {}

    def _get_redis(self) -> Optional[redis.Redis]:
        """Tenta obter uma conexão com o Redis."""
        if self._redis_client is not None:
            try:
                self._redis_client.ping()
                return self._redis_client
            except Exception:
                self._redis_client = None

        redis_urls = [
            os.environ.get("REDIS_URL"),
            os.environ.get("CELERY_BROKER_URL"),
            "redis://redis:6379/0",
            "redis://127.0.0.1:6379/0",
            "redis://127.0.0.1:3080/0",
        ]

        for url in redis_urls:
            if not url:
                continue
            try:
                client = redis.Redis.from_url(url, socket_timeout=1.5, socket_connect_timeout=1.5)
                client.ping()
                self._redis_client = client
                return client
            except Exception:
                continue

        return None

    def record_call(self, model_id: str, tokens: int = 0) -> None:
        """Registra uma requisição e a quantidade de tokens consumidos no modelo."""
        normalized_id = model_id.lower().strip()
        now_ts = int(time.time())
        current_minute = now_ts // 60
        current_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        r = self._get_redis()
        if r:
            try:
                pipe = r.pipeline()
                key_rpm = f"rate_limit:{normalized_id}:rpm:{current_minute}"
                key_tpm = f"rate_limit:{normalized_id}:tpm:{current_minute}"
                key_rpd = f"rate_limit:{normalized_id}:rpd:{current_day}"

                pipe.incrby(key_rpm, 1)
                pipe.expire(key_rpm, 120)
                if tokens > 0:
                    pipe.incrby(key_tpm, tokens)
                    pipe.expire(key_tpm, 120)
                pipe.incrby(key_rpd, 1)
                pipe.expire(key_rpd, 172800)
                pipe.execute()
                return
            except Exception as e:
                logger.warning(f"Falha ao registrar no Redis, utilizando fallback em memória: {e}")

        # Memory Fallback
        if normalized_id not in self._memory_rpm:
            self._memory_rpm[normalized_id] = {}
            self._memory_tpm[normalized_id] = {}
            self._memory_rpd[normalized_id] = {}

        self._memory_rpm[normalized_id][current_minute] = (
            self._memory_rpm[normalized_id].get(current_minute, 0) + 1
        )
        if tokens > 0:
            self._memory_tpm[normalized_id][current_minute] = (
                self._memory_tpm[normalized_id].get(current_minute, 0) + tokens
            )
        self._memory_rpd[normalized_id][current_day] = (
            self._memory_rpd[normalized_id].get(current_day, 0) + 1
        )

        # Limpeza de minutos antigos
        for m_id in list(self._memory_rpm.keys()):
            for min_key in list(self._memory_rpm[m_id].keys()):
                if min_key < current_minute - 5:
                    del self._memory_rpm[m_id][min_key]
            for min_key in list(self._memory_tpm[m_id].keys()):
                if min_key < current_minute - 5:
                    del self._memory_tpm[m_id][min_key]

    def get_metrics(self, model_id: str) -> Dict[str, int]:
        """Obtém as métricas atuais de RPM, TPM e RPD para um determinado modelo."""
        normalized_id = model_id.lower().strip()
        now_ts = int(time.time())
        current_minute = now_ts // 60
        current_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        rpm = 0
        tpm = 0
        rpd = 0

        r = self._get_redis()
        if r:
            try:
                key_rpm = f"rate_limit:{normalized_id}:rpm:{current_minute}"
                key_tpm = f"rate_limit:{normalized_id}:tpm:{current_minute}"
                key_rpd = f"rate_limit:{normalized_id}:rpd:{current_day}"

                val_rpm = r.get(key_rpm)
                val_tpm = r.get(key_tpm)
                val_rpd = r.get(key_rpd)

                rpm = int(val_rpm) if val_rpm else 0
                tpm = int(val_tpm) if val_tpm else 0
                rpd = int(val_rpd) if val_rpd else 0
                return {"rpm": rpm, "tpm": tpm, "rpd": rpd}
            except Exception as e:
                logger.warning(f"Falha ao ler métricas do Redis: {e}")

        # Memory Fallback
        if normalized_id in self._memory_rpm:
            rpm = self._memory_rpm[normalized_id].get(current_minute, 0)
        if normalized_id in self._memory_tpm:
            tpm = self._memory_tpm[normalized_id].get(current_minute, 0)
        if normalized_id in self._memory_rpd:
            rpd = self._memory_rpd[normalized_id].get(current_day, 0)

        return {"rpm": rpm, "tpm": tpm, "rpd": rpd}

    def get_all_models_status(self) -> List[Dict[str, Any]]:
        """Retorna o status completo de todos os modelos monitorados no sistema."""
        status_list = []
        for model_id, cfg in self._models_config.items():
            metrics = self.get_metrics(model_id)
            rpm_curr = metrics["rpm"]
            tpm_curr = metrics["tpm"]
            rpd_curr = metrics["rpd"]

            rpm_limit = cfg["rpm_limit"]
            tpm_limit = cfg["tpm_limit"]
            rpd_limit = cfg["rpd_limit"]

            # Calcula o percentual de uso em relação ao limite mais restrito
            rpm_pct = (rpm_curr / rpm_limit * 100) if rpm_limit > 0 else 0
            tpm_pct = (tpm_curr / tpm_limit * 100) if tpm_limit > 0 else 0
            rpd_pct = (rpd_curr / rpd_limit * 100) if rpd_limit > 0 else 0

            max_pct = max(rpm_pct, tpm_pct, rpd_pct)

            if max_pct >= 85:
                status_level = "danger"
            elif max_pct >= 60:
                status_level = "warning"
            else:
                status_level = "ok"

            status_list.append(
                {
                    "id": cfg["id"],
                    "name": cfg["name"],
                    "category": cfg["category"],
                    "rpm": rpm_curr,
                    "rpm_limit": rpm_limit,
                    "rpm_pct": round(rpm_pct, 1),
                    "tpm": tpm_curr,
                    "tpm_limit": tpm_limit,
                    "tpm_pct": round(tpm_pct, 1),
                    "rpd": rpd_curr,
                    "rpd_limit": rpd_limit,
                    "rpd_pct": round(rpd_pct, 1),
                    "max_pct": round(max_pct, 1),
                    "status": status_level,
                }
            )
        return status_list

    def update_model_limits(
        self, model_id: str, rpm_limit: Optional[int] = None, tpm_limit: Optional[int] = None, rpd_limit: Optional[int] = None
    ) -> bool:
        """Atualiza os limites operacionais configurados para um modelo."""
        normalized_id = model_id.lower().strip()
        if normalized_id not in self._models_config:
            return False

        if rpm_limit is not None and rpm_limit > 0:
            self._models_config[normalized_id]["rpm_limit"] = rpm_limit
        if tpm_limit is not None and tpm_limit > 0:
            self._models_config[normalized_id]["tpm_limit"] = tpm_limit
        if rpd_limit is not None and rpd_limit > 0:
            self._models_config[normalized_id]["rpd_limit"] = rpd_limit
        return True

    def reset_metrics(self) -> None:
        """Reseta contadores de métricas em memória e Redis para testes."""
        r = self._get_redis()
        if r:
            try:
                keys = r.keys("rate_limit:*")
                if keys:
                    r.delete(*keys)
            except Exception:
                pass
        self._memory_rpm.clear()
        self._memory_tpm.clear()
        self._memory_rpd.clear()


# Singleton global
rate_limiter = ModelRateLimiter()
