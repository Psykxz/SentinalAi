# from django import template

# register = template.Library()

# @register.filter
# def replace_chars(value, arg):
#     """
#     Replaces all occurrences of a substring in a string.
#     Usage: {{ value|replace_chars:"old_char|new_char" }}
#     e.g. {{ category|replace_chars:"_ | " }}
#     """
#     if value and arg:
#         try:
#             old, new = arg.split("|")
#             return value.replace(old.strip(), new.strip())
#         except ValueError:
#             # Handle cases where the argument format is incorrect
#             return value
#     return value

from django import template

register = template.Library()

@register.filter
def replace_chars(value, arg):
    """
    Replaces all occurrences of a substring in a string.
    Usage: {{ value|replace_chars:"old_char|new_char" }}
    e.g. {{ category|replace_chars:"_ | " }}
    """
    if value and arg:
        try:
            # Note: We keep the strip() calls for robustness
            old, new = arg.split("|")
            return value.replace(old.strip(), new.strip())
        except ValueError:
            # Handle cases where the argument format is incorrect
            return value
    return value


@register.filter
def sub(value, arg):
    """
    Subtracts the arg from the value.
    Usage: {{ value|sub:arg }}
    """
    try:
        # Convert to float to handle both integers and decimal values
        return float(value) - float(arg)
    except (ValueError, TypeError):
        # Return 0 or the original value in case of non-numeric input
        return 0


@register.filter
def percentage(value, arg):
    """
    Calculates the percentage of value relative to arg, rounded to the nearest whole number.
    Usage: {{ value|percentage:total }}
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        # Calculates (value / arg) * 100 and rounds to 0 decimal places
        return round((value / arg) * 100)
    except (ValueError, TypeError):
        return 0