def generate_distinct_colors(n):
    """
    Генерирует n различных цветов в hex-формате (для Tkinter).
    Цвета подбираются вручную из палитры, безопасной для чтения на светлом фоне.
    """
    base_colors = [
        "#1f77b4",  # синий
        "#2ca02c",  # зелёный
        "#ff7f0e",  # оранжевый
        "#d62728",  # красный
        "#9467bd",  # фиолетовый
        "#8c564b",  # коричневый
        "#e377c2",  # розовый
        "#7f7f7f",  # серый
        "#bcbd22",  # оливковый
        "#17becf",  # голубой
    ]
    return base_colors[:n] if n <= len(base_colors) else base_colors * (n // len(base_colors) + 1)
