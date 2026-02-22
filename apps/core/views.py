# Create your views here.
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

logger = logging.getLogger(__name__)


class UserOwnedQuerysetMixin(LoginRequiredMixin):
    """Filtra queryset por usuario autenticado."""

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class UserFormKwargsMixin:
    """Pasa user al form via kwargs."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class UserOwnedListView(UserOwnedQuerysetMixin, ListView):
    """ListView base con filtro por usuario y paginación."""

    paginate_by = 20


class UserOwnedCreateView(UserOwnedQuerysetMixin, UserFormKwargsMixin, CreateView):
    """CreateView base que asigna user al objeto."""

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response

    def get_success_message(self):
        return "Registro creado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context


class UserOwnedUpdateView(UserOwnedQuerysetMixin, UserFormKwargsMixin, UpdateView):
    """UpdateView base con filtro por usuario."""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response

    def get_success_message(self):
        return "Registro actualizado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


class UserOwnedDeleteView(UserOwnedQuerysetMixin, DeleteView):
    """DeleteView base con mensaje de éxito."""

    def form_valid(self, form):
        obj = self.get_object()
        success_url = self.get_success_url()
        obj.delete()
        messages.success(self.request, self.get_success_message(obj))
        return HttpResponseRedirect(success_url)

    def get_success_message(self, obj):
        return "Registro eliminado correctamente."


class UserOwnedDetailView(UserOwnedQuerysetMixin, DetailView):
    """DetailView base con filtro por usuario."""

    pass
