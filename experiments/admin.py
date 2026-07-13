from django.contrib import admin
from .models import Experiment


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'complete', 'slug', 'created_at')
    list_filter = ('complete',)
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'created_at', 'updated_at')
