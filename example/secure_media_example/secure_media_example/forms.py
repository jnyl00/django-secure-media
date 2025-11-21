from django import forms


UPLOAD_FOLDER_CHOICES = [('profiles', "profiles/"), ("general", "general/"), ('images', "images/")]


class FileUploadForm(forms.Form):
    upload_to = forms.ChoiceField(
        choices=UPLOAD_FOLDER_CHOICES, widget=forms.RadioSelect(), initial=UPLOAD_FOLDER_CHOICES[0]
    )
    file = forms.FileField(required=True)
