import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import TradeForm
from .models import Trade


class UserQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)


class TradeListView(UserQuerysetMixin, ListView):
    model = Trade
    template_name = 'trades/list.html'
    context_object_name = 'trades'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        result = self.request.GET.get('result', '')
        pair = self.request.GET.get('pair', '')

        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(paire__icontains=q) | Q(strategie__icontains=q) | Q(commentaires__icontains=q)
            )
        if result == 'gain':
            qs = qs.filter(resultat_monetaire__gt=0)
        elif result == 'loss':
            qs = qs.filter(resultat_monetaire__lte=0)
        if pair:
            qs = qs.filter(paire=pair)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['result'] = self.request.GET.get('result', '')
        ctx['pair'] = self.request.GET.get('pair', '')
        ctx['pairs'] = Trade.PAIR_CHOICES
        return ctx


class TradeCreateView(LoginRequiredMixin, CreateView):
    model = Trade
    form_class = TradeForm
    template_name = 'trades/form.html'
    success_url = reverse_lazy('trades:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Trade ajouté avec succès.')
        return super().form_valid(form)


class TradeUpdateView(UserQuerysetMixin, UpdateView):
    model = Trade
    form_class = TradeForm
    template_name = 'trades/form.html'
    success_url = reverse_lazy('trades:list')

    def form_valid(self, form):
        messages.success(self.request, 'Trade mis à jour.')
        return super().form_valid(form)


class TradeDeleteView(UserQuerysetMixin, DeleteView):
    model = Trade
    template_name = 'trades/confirm_delete.html'
    success_url = reverse_lazy('trades:list')

    def form_valid(self, form):
        messages.success(self.request, 'Trade supprimé.')
        return super().form_valid(form)


def export_csv_view(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trades_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Date ouverture', 'Date fermeture', 'Paire', 'Direction', 'Taille', 'Stratégie',
        'Session', 'Prix entrée', 'Prix sortie', 'Stop Loss', 'Take Profit',
        'Résultat (pips)', 'Résultat (devise)', 'Commission/Swap', 'Humeur avant',
        'Humeur après', 'Respect du plan', 'Commentaires',
    ])
    for t in Trade.objects.filter(user=request.user):
        writer.writerow([
            t.date_ouverture, t.date_fermeture, t.paire, t.get_direction_display(), t.taille,
            t.strategie, t.session, t.prix_entree, t.prix_sortie, t.stop_loss, t.take_profit,
            t.resultat_pips, t.resultat_monetaire, t.commission_swap, t.humeur_avant,
            t.humeur_apres, 'Oui' if t.respect_plan else 'Non', t.commentaires,
        ])
    return response
