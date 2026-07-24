import math
import os


def get_concurrency_config(cpu_cores: int | None = None) -> dict:
    """
    Calcula a capacidade total de concorrência e a divisão entre as filas.

    Regras:
    - Fórmula Total: Math.floor(CPU_CORES * 0.70) (com mínimo global de 4 processos)
    - Divisão: O total é compartilhado entre a fila de 'analises' e 'envios'
    - Mínimo de 2 trabalhadores por fila em máquinas menores.

    Exemplo para 16 cores:
    - Total: 16 * 0.70 = 11.2 -> floor = 11
    - Fila de Análise: 6
    - Fila de Envio: 5
    """
    if cpu_cores is None:
        cpu_cores = os.cpu_count() or 1
    elif cpu_cores < 1:
        cpu_cores = 1

    total = max(4, math.floor(cpu_cores * 0.70))
    analises = max(2, math.ceil(total / 2))
    envios = max(2, math.floor(total / 2))

    return {
        "cpu_cores": cpu_cores,
        "total": total,
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
