import rules
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from .models import Experiment
from .forms import ExperimentForm, TermsForm
from .xlsx import generate_xlsx


def _own_or_404(user, experiment, perm='experiments.view_experiment'):
    if not rules.has_perm(perm, user, experiment):
        raise Http404


@method_decorator(login_required, name='dispatch')
class ExperimentListView(ListView):
    template_name = 'experiments/index.html'
    context_object_name = 'experiments'

    def get_queryset(self):
        return Experiment.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class ExperimentCreateView(CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'experiments/new.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Experiment created.')
        return response

    def get_success_url(self):
        return reverse('experiments:show', kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class ExperimentDetailView(DetailView):
    template_name = 'experiments/show.html'

    def get_object(self):
        obj = get_object_or_404(Experiment, pk=self.kwargs['pk'])
        _own_or_404(self.request.user, obj)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        exp = self.object
        pk = exp.pk
        ctx['total_responses'] = exp.total_responses()
        ctx['finished_responses'] = exp.finished_responses()
        ctx['last_response_date'] = exp.last_response_date()
        ctx['tasks'] = exp.tasks.order_by('sort').select_related()
        ctx['completion_errors'] = self.request.session.pop(f'exp_{pk}_errors', None)
        ctx['completion_warnings'] = self.request.session.pop(f'exp_{pk}_warnings', None)
        ctx['completion_force'] = self.request.session.pop(f'exp_{pk}_force', False)
        return ctx


@method_decorator(login_required, name='dispatch')
class ExperimentUpdateView(UpdateView):
    form_class = ExperimentForm
    template_name = 'experiments/edit.html'

    def get_object(self):
        obj = get_object_or_404(Experiment, pk=self.kwargs['pk'])
        _own_or_404(self.request.user, obj, 'experiments.change_experiment')
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Experiment saved.')
        return response

    def get_success_url(self):
        return reverse('experiments:show', kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class ExperimentDeleteView(DeleteView):
    success_url = reverse_lazy('experiments:index')

    def get_object(self):
        obj = get_object_or_404(Experiment, pk=self.kwargs['pk'])
        _own_or_404(self.request.user, obj, 'experiments.delete_experiment')
        return obj


@method_decorator(login_required, name='dispatch')
class ExperimentDownloadView(View):
    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        buf = generate_xlsx(exp)
        safe_name = exp.name.lower().replace(' ', '_')
        filename = f"{safe_name}_results.xlsx"
        return FileResponse(
            buf, as_attachment=True, filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )


@method_decorator(login_required, name='dispatch')
class ExperimentCompleteView(View):
    def post(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp, 'experiments.change_experiment')

        if exp.complete:
            exp.complete = False
            exp.save(update_fields=['complete'])
            messages.success(request, 'Experiment unpublished.')
            return redirect('experiments:show', pk=pk)

        result = exp.completion_errors()
        errs = result['errors']
        warns = result['warnings']

        if errs:
            request.session[f'exp_{pk}_errors'] = errs
            request.session[f'exp_{pk}_warnings'] = warns
            return redirect('experiments:show', pk=pk)

        if warns and not request.POST.get('force'):
            request.session[f'exp_{pk}_warnings'] = warns
            request.session[f'exp_{pk}_force'] = True
            return redirect('experiments:show', pk=pk)

        exp.complete = True
        exp.save(update_fields=['complete'])
        request.session.pop(f'exp_{pk}_errors', None)
        request.session.pop(f'exp_{pk}_warnings', None)
        request.session.pop(f'exp_{pk}_force', None)
        messages.success(request, 'Experiment published.')
        return redirect('experiments:show', pk=pk)


@method_decorator(login_required, name='dispatch')
class ExperimentTermsView(UpdateView):
    form_class = TermsForm
    template_name = 'experiments/terms.html'

    def get_object(self):
        obj = get_object_or_404(Experiment, pk=self.kwargs['pk'])
        _own_or_404(self.request.user, obj, 'experiments.change_experiment')
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Terms saved.')
        return response

    def get_success_url(self):
        return reverse('experiments:show', kwargs={'pk': self.object.pk})
