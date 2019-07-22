from django import forms
import datetime
import json, requests


class UserForm(forms.Form):

    def hitAPI():
        start = datetime.date.today()
        tdelta = datetime.timedelta(days=1)
        end = start + tdelta

        if start.weekday() == 5 or start.weekday() == 6:
            tdel = datetime.timedelta(days=2)
            start -= tdel
            end = start + tdelta
        base = 'USD'

        data = requests.get(f"https://api.exchangeratesapi.io/history?start_at={start}&"
                            f"end_at={end}&base={base}")

        data = json.loads(data.text)
        curr = list(data['rates'][str(start)].keys())
        curr.append(base)
        return curr

    CHOICES = list(enumerate(hitAPI()))

    now = datetime.date.today()

    base_Currency = forms.ChoiceField(widget=forms.Select, choices=CHOICES, initial='USD')
    target_Currency = forms.ChoiceField(widget=forms.Select, choices=CHOICES, initial='INR')
    amount = forms.IntegerField()
    startDate = forms.DateField(widget=forms.DateInput, initial=now)
    max_waiting_time = forms.IntegerField()

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        base = cleaned_data.get('base_Currency')
        target = cleaned_data.get('target_Currency')
        time = cleaned_data.get('max_waiting_time')

        if base and target and base == target:
            self._errors['target_conf'] = self.error_class(['Cannot be same'])
            del self.cleaned_data['target_Currency']
            raise forms.ValidationError("Base and Target currencies can't be the same")
        if time < 1 or time > 6:
            raise forms.ValidationError("Max Waiting time takes values between 1 and 6 only")
        
        return cleaned_data
