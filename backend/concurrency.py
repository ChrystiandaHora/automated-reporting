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
    env_envios = os.environ.get("CELERY_CONCURRENCY_ENVIOS")
    env_analises = os.environ.get("CELERY_CONCURRENCY_ANALISES")

    if env_envios and env_envios.isdigit() and env_analises and env_analises.isdigit():
        c_envios = int(env_envios)
        c_analises = int(env_analises)
        return {
            "cpu_cores": cpu_cores,
            "total": c_envios + c_analises,
            "dynamic_sharing": True,
            "queues": {
                "analises": c_analises,
                "envios": c_envios,
            },
        }

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

    # Cálculo dinâmico baseado nos núcleos de CPU (70% do total)
    if cpu_cores >= 14:
        analises = 4
        envios = 8
    elif cpu_cores >= 8:
        analises = 3
        envios = 5
    elif cpu_cores >= 4:
        analises = 2
        envios = 3
    else:
        analises = 1
        envios = 2

    return {
        "cpu_cores": cpu_cores,
        "total": analises + envios,
        "dynamic_sharing": True,
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
