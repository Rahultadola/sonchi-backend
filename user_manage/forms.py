from django.forms import ModelForm

from .models import Question, Answer, Guest


class QuestionForm(ModelForm):
	class Meta:
		model = Question
		fields = Question.get_attributes()



class AnswerForm(ModelForm):
	class Meta:
		model = Answer
		fields = Answer.get_attributes()


class GuestForm(ModelForm):
	class Meta:
		model = Guest
		fields = Guest.get_attributes()