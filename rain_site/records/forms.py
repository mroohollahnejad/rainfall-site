
from django import forms
import jdatetime
from .models import RainRecord, Station

class RainRecordForm(forms.ModelForm):
    # separate jalali fields for user-friendly input
    jy = forms.IntegerField(label='سال (شمسی)')
    jm = forms.IntegerField(label='ماه (شمسی)')
    jd = forms.IntegerField(label='روز (شمسی)')
    hour = forms.IntegerField(label='ساعت', min_value=0, max_value=23)
    minute = forms.IntegerField(label='دقیقه', min_value=0, max_value=59)

    class Meta:
        model = RainRecord
        fields = ['station', 'rainfall_mm']

    def clean(self):
        cleaned = super().clean()
        jy = cleaned.get('jy')
        jm = cleaned.get('jm')
        jd = cleaned.get('jd')
        hour = cleaned.get('hour')
        minute = cleaned.get('minute')
        try:
            jalali = jdatetime.datetime(jy, jm, jd, hour, minute)
            greg = jalali.togregorian()
            cleaned['timestamp'] = greg
        except Exception as e:
            raise forms.ValidationError('تاریخ یا زمان نامعتبر است: ' + str(e))
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.timestamp = self.cleaned_data['timestamp']
        if commit:
            obj.save()
        return obj
