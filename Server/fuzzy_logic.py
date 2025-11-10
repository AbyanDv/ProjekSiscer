def fuzzy_level(total_hours):
    """Menentukan level screen time berdasarkan total jam"""
    if total_hours <= 2:
        return "Low"
    elif total_hours <= 5:
        return "Moderate"
    else:
        return "High"