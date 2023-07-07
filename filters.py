# def format_currency(value, currency_symbol='₦', decimal_separator='.', thousands_separator=','):
#     formatted_value = f'{currency_symbol}{value:,.2f}'
#     return formatted_value.replace('.', decimal_separator).replace(',', thousands_separator)

def format_currency(value, currency_symbol='₦', decimal_separator='.', thousands_separator=','):
    # Check if the value is negative
    if value < 0:
        # Remove the negative sign and format the absolute value
        formatted_value = f'-{currency_symbol}{abs(value):,.2f}'
    else:
        # Format the positive value
        formatted_value = f'{currency_symbol}{value:,.2f}'

    # Replace the decimal separator and thousands separator
    formatted_value = formatted_value.replace('.', decimal_separator).replace(',', thousands_separator)

    return formatted_value
