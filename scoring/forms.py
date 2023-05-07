from django import forms
from django.core.validators import FileExtensionValidator

class UploadFileForm(forms.Form):
    file = forms.FileField(
    	label = 'Unggah file excel (xlsx, xls) dengan format yang ditentukan ',
    	widget = forms.FileInput(
    			attrs = {
    				'class' : 'form-control',
    			}
    		),
    	validators=[FileExtensionValidator( ['xlsx', 'xls'] ) ]
    	)

class InputParameterForm(forms.Form):
	kValue = forms.ChoiceField(
			label = 'Nilai k ',
			choices = [
				(2, '2'),
				(3, '3'),
				(5, '5'),
				(7, '7'),
				(9, '9'),
			],
			widget = forms.Select(
					attrs = {
						'class' : 'form-select'
					}
				)
		)
	bValue = forms.ChoiceField(
			label = 'Nilai b ',
			choices = [
				(2, '2'),
				(3, '3'),
				(5, '5'),
				(7, '7'),
				(11, '11'),
				(13, '13'),
				(17, '17'),
				(19, '19'),
				(23, '23'),
			],
			widget = forms.Select(
					attrs = {
						'class' : 'form-select'
					}
				)
		)
	synonym = forms.BooleanField(
			required = False,
			label = 'synonym ',
			widget = forms.CheckboxInput(
					attrs = {
						'class' : 'form-check-input'
					}
				)
		)