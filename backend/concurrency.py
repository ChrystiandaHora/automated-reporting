import math
import os


def get_concurrency_config(cpu_cores: int | None = None) -> dict:
    """
    Calcula a capacidade total de concorrência e a divisão entre as filas.

    Fórmula:
    - Total de processos no sistema: Math.floor(CPU_CORES * 0.70) (com mínimo global de 4)
    - Fila de Análise (analises): ceil(Total / 2)
    - Fila de Lançamento (envios): floor(Total / 2)
    """
    if cpu_cores is None:
        cpu_cores = os.cpu_count() or 1
    elif cpu_cores < 1:
        cpu_cores = 1

    env_override = os.environ.get("CELERY_CONCURRENCY") or os.environ.get("CELERY_WORKER_CONCURRENCY")
    if env_override and env_override.isdigit():
        custom = int(env_override)
        return {
            "cpu_cores": cpu_cores,
            "total": custom * 2,
            "dynamic_sharing": True,
            "queues": {
                "analises": custom,
                "envios": custom,
            },
        }

    analises = 3
    # 4 envios simultâneos para automação no portal Munka
    envios = 4

    return {
        "cpu_cores": cpu_cores,
        "total": analises + envios,
        "dynamic_sharing": False,
        "queues": {
            "analises": analises,
            "envios": envios,
        },
    }


def calculate_queue_concurrency(
    queue_name: str | None = None, cpu_cores: int | None = None
) -> int:
    """
    Retorna a concorrência específica para a fila informada ('analises' ou 'envios').
    Se nenhuma fila for especificada, tenta obter via variável de ambiente CELERY_QUEUE
    ou retorna o valor da fila de análises como padrão.
    """
    if not queue_name:
        queue_name = os.environ.get("CELERY_QUEUE", "analises")

    config = get_concurrency_config(cpu_cores)
    return config["queues"].get(queue_name, config["queues"]["analises"])


if __name__ == "__main__":
    cfg = get_concurrency_config()
    print(f"CPU Cores detectados: {cfg['cpu_cores']}")
    print(f"Total de Concorrência do Sistema: {cfg['total']}")
    print(f"  • Fila de Análise (analises): {cfg['queues']['analises']} workers")
    print(f"  • Fila de Lançamento (envios): {cfg['queues']['envios']} workers")
