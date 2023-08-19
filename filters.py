def format_currency(
    value, currency_symbol="₦", decimal_separator=".", thousands_separator=","
):
    # Check if the value is negative
    if value:
        if value < 0:
            # Remove the negative sign and format the absolute value
            formatted_value = f"-{currency_symbol}{abs(value):,.2f}"
        else:
            # Format the positive value
            formatted_value = f"{currency_symbol}{value:,.2f}"

        # Replace the decimal separator and thousands separator
        formatted_value = formatted_value.replace(".", decimal_separator).replace(
            ",", thousands_separator
        )
    else:
        formatted_value = f"{currency_symbol}0"

    return formatted_value


# def render_template_with_currency(template_name, **context):
#     # Create the Jinja2 environment
#     env = Environment(loader=FileSystemLoader('./templates'))
#     # Register the custom filter
#     env.filters['currency'] = format_currency

#     # Render the template with the provided context
#     template = env.get_template(template_name)
#     output = template.render(**context)

#     return output
