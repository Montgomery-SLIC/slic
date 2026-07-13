from django.contrib import admin
from .models import (
    Task, QuestionTask, SampleTask, ListeningTask, ClickTask,
    IntermediateScreenTask, Question, Option, Scale,
)

admin.site.register(Task)
admin.site.register(QuestionTask)
admin.site.register(SampleTask)
admin.site.register(ListeningTask)
admin.site.register(ClickTask)
admin.site.register(IntermediateScreenTask)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Scale)
