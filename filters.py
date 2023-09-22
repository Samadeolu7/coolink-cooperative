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


from dateutil.relativedelta import relativedelta

# def calculate_duration_in_months(start_date, end_date):
#     duration = relativedelta(end_date, start_date)
#     months = duration.months
#     years = duration.years
#     total_months = years * 12 + months
#     return total_months

from dateutil.relativedelta import relativedelta

def calculate_duration_in_months(start_date, end_date):
    duration = relativedelta(end_date, start_date)
    months = duration.months
    years = duration.years

    if years > 0:
        if months > 0:
            return f"{years} years and {months} months"
        elif years == 1:
            return f"{years} year"
        else:
            return f"{years} years"
    else:
        return f"{months} months"
