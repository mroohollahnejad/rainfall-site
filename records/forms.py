from django import forms
from .models import RainRecord, Station
import jdatetime

class RainRecordForm(forms.ModelForm):
    # انتخاب ایستگاه از لیست ثابت در مدل
    station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label='ایستگاه',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # تاریخ شمسی به صورت دستی وارد می‌شود یا با تقویم
    date = forms.CharField(
        label='تاریخ (به صورت شمسی: YYYY/MM/DD)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 1403/07/25'})
    )

    hour = forms.IntegerField(
        label='ساعت',
        min_value=0,
        max_value=23,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0 تا 23'})
    )

    minute = forms.IntegerField(
        label='دقیقه',
        min_value=0,
        max_value=59,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0 تا 59'})
    )

    rainfall_mm = forms.DecimalField(
        label='میزان بارش (میلیمتر)',
        min_value=0,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً 12.5'})
    )

    class Meta:
        model = RainRecord
        fields = ['station', 'date', 'hour', 'minute', 'rainfall_mm']

    def clean(self):
        cleaned_data = super().clean()
        date_str = cleaned_data.get('date')
        hour = cleaned_data.get('hour')
        minute = cleaned_data.get('minute')

        if date_str and hour is not None and minute is not None:
            try:
                # تبدیل تاریخ شمسی به میلادی
                jdate = jdatetime.datetime.strptime(date_str, '%Y/%m/%d')
                gregorian_dt = jdate.replace(hour=hour, minute=minute).togregorian()
                cleaned_data['timestamp'] = gregorian_dt
            except Exception as e:
                raise forms.ValidationError(f"تاریخ یا زمان وارد شده معتبر نیست: {e}")

        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.timestamp = self.cleaned_data['timestamp']
        if commit:
            obj.save()
        return obj
