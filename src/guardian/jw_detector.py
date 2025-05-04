from typing import List

import textdistance


def is_rewrite(a: List[str], b: List[str], threshold: float = 0.92) -> bool:
    """Determina si dos historiales de commits son reescrituras similares.
    Args:
        a, b: Listas de SHAs de commits ordenadas (raíz → punta).
        threshold: Umbral de similitud Jaro-Winkler (0.0 a 1.0).
    Returns:
        True si la similitud ≥ threshold.
    """
    str_a = "".join(a)
    str_b = "".join(b)
    return textdistance.jaro_winkler(str_a, str_b) >= threshold
