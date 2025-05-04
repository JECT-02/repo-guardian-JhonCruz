from guardian.jw_detector import is_rewrite


def test_is_rewrite_similar_commits():
    """Prueba cuando las listas de commits son muy similares (similitud ≥ umbral)."""
    a = ["abc123", "def456"]
    b = ["abc123", "def789"]
    assert is_rewrite(a, b, threshold=0.8) is True

def test_is_rewrite_different_commits():
    """Prueba cuando las listas de commits son diferentes (similitud < umbral)."""
    a = ["abc123", "def456"]
    b = ["xyz789", "uvw123"]
    assert is_rewrite(a, b, threshold=0.9) is False

def test_is_rewrite_empty_lists():
    """Prueba con listas vacías."""
    a = []
    b = []
    assert is_rewrite(a, b, threshold=0.9) is True

def test_is_rewrite_different_lengths():
    """Prueba con listas de diferentes longitudes y contenido distinto."""
    a = ["abc123", "def456", "ghi789"]
    b = ["xyz789", "uvw123"]
    assert is_rewrite(a, b, threshold=0.9) is False

def test_is_rewrite_custom_threshold():
    """Prueba con umbrales personalizados que cambian el resultado."""
    a = ["abc123", "def456"]
    b = ["abc123", "def789"]
    assert is_rewrite(a, b, threshold=0.99) is False  # Umbral restrictivo
    assert is_rewrite(a, b, threshold=0.7) is True   # Umbral permisivo
