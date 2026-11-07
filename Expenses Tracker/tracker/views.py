import csv
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import SignUpForm, ExpenseForm
from .models import Expense
from .utils import predict_category


class CustomLoginView(LoginView):
    template_name = 'tracker/login.html'


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'tracker/signup.html', {'form': form})


def _filter_by_period(qs, period):
    today = timezone.localdate()
    if period == 'today':
        return qs.filter(date=today)
    if period == 'week':
        start = today - timedelta(days=today.weekday())
        return qs.filter(date__gte=start, date__lte=today)
    if period == 'month':
        return qs.filter(date__year=today.year, date__month=today.month)
    return qs


@login_required
def dashboard(request):
    period = request.GET.get('period', 'month')
    expenses_qs = Expense.objects.filter(user=request.user)
    filtered = _filter_by_period(expenses_qs, period)

    total = filtered.aggregate(total=Sum('amount'))['total'] or 0
    category_totals = (
        filtered.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    chart_labels = [c['category'] for c in category_totals]
    chart_values = [float(c['total']) for c in category_totals]

    context = {
        'expenses': filtered[:10],
        'total': total,
        'period': period,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'expense_count': filtered.count(),
    }
    return render(request, 'tracker/dashboard.html', context)


@login_required
def expense_list(request):
    period = request.GET.get('period', 'all')
    category = request.GET.get('category', '')

    expenses = Expense.objects.filter(user=request.user)
    expenses = _filter_by_period(expenses, period)
    if category:
        expenses = expenses.filter(category=category)

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'expenses': expenses,
        'period': period,
        'selected_category': category,
        'categories': Expense.CATEGORY_CHOICES,
        'total': total,
    }
    return render(request, 'tracker/expense_list.html', context)


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            # If the user left the auto-suggested category untouched but the
            # description changed, this still respects whatever the user picked.
            expense.save()
            messages.success(request, 'Expense added successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(initial={'date': timezone.localdate()})
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expense_list')
    return render(request, 'tracker/expense_confirm_delete.html', {'expense': expense})


@login_required
def predict_category_api(request):
    """Small JSON endpoint used by the add/edit form to live-suggest a category."""
    description = request.GET.get('description', '')
    return HttpResponse(
        json.dumps({'category': predict_category(description)}),
        content_type='application/json',
    )


@login_required
def download_csv(request):
    expenses = Expense.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Notes'])
    for e in expenses:
        writer.writerow([e.date, e.description, e.category, e.amount, e.notes or ''])
    return response


@login_required
def download_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    expenses = Expense.objects.filter(user=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expense_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Expense Report - {request.user.username}", styles['Title']), Spacer(1, 12)]

    data = [['Date', 'Description', 'Category', 'Amount', 'Notes']]
    total = 0
    for e in expenses:
        data.append([str(e.date), e.description, e.category, f"{e.amount}", e.notes or ''])
        total += float(e.amount)
    data.append(['', '', '', f"Total: {total:.2f}", ''])

    table = Table(data, colWidths=[60 * mm / 3, 45 * mm, 30 * mm, 30 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eef2ff')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    doc.build(elements)
    return response
