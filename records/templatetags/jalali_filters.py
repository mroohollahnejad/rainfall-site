import jdatetime
from django import template

register = template.Library()

@register.filter
def jalali_date(value, date_format="%Y/%m/%d"):
    """
    تبدیل تاریخ میلادی به شمسی
    استفاده در قالب: {{ obj.timestamp|jalali_date }}
    """
    if value is None:
        return ""
    try:
        # اگر value با timezone aware است
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            value = value.astimezone()
        j_date = jdatetime.datetime.fromgregorian(datetime=value)
        return j_date.strftime(date_format)
    except Exception:
        return value
