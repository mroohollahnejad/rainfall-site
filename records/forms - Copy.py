from django import forms
from .models import RainRecord, Station

class RainRecordForm(forms.ModelForm):
    # انتخاب ایستگاه از لیست مدل
    station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label='ایستگاه',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # میزان بارش
    rainfall_mm = forms.DecimalField(
        label='میزان بارش (میلیمتر)',
        min_value=0,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً 12.5'})
    )

    class Meta:
        model = RainRecord
        # فقط فیلدهای واقعی مدل
        fields = ['station', 'rainfall_mm']

# فرم ورود (Login) بدون تغییر
class LoginForm(forms.Form):
    username = forms.CharField(
        label="نام کاربری",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری خود را وارد کنید'})
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'})
    )
    remember_me = forms.BooleanField(
        required=False,
        label="مرا به خاطر بسپار",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
