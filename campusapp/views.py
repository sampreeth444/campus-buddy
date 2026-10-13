import os

from django.db.models import F
from django.http import Http404
from django.shortcuts import render

from .models import PageVisit


def count_visit(request, page):
    """Count one page open. Skips form submissions and UptimeRobot pings."""
    if request.method != 'GET':
        return
    agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'uptimerobot' in agent:
        return
    visit, _ = PageVisit.objects.get_or_create(page=page)
    PageVisit.objects.filter(pk=visit.pk).update(count=F('count') + 1)


def home(request):
    count_visit(request, 'home')
    return render(request, 'home.html')


def help_page(request):
    count_visit(request, 'help')
    return render(request, 'help.html')


def attendance_calculator(request):
    count_visit(request, 'attendance')
    result = None
    error = None
    if request.method == 'POST':
        try:
            total = float(request.POST.get('total'))
            attended = float(request.POST.get('attended'))
            skip = float(request.POST.get('skip', 0) or 0)

            if attended > total or total <= 0 or attended < 0:
                error = "Check your numbers — attended can't exceed total."
            else:
                percentage = (attended / total) * 100
                classes_needed = 0
                classes_can_miss = 0
                if percentage < 75:
                    classes_needed = int(((0.75 * total) - attended) / 0.25) + 1
                else:
                    classes_can_miss = int((attended / 0.75) - total)

                new_total = total + skip
                new_percentage = round((attended / new_total) * 100, 2) if skip > 0 else None

                result = {
                    'percentage': round(percentage, 2),
                    'classes_needed': classes_needed,
                    'classes_can_miss': classes_can_miss,
                    'new_percentage': new_percentage,
                    'skip': int(skip) if skip else 0,
                }
        except (ValueError, TypeError):
            error = "Enter valid numbers."
    return render(request, 'attendance.html', {'result': result, 'error': error})


def marks_calculator(request):
    count_visit(request, 'marks')
    result = None
    error = None
    if request.method == 'POST':
        try:
            t1_raw = request.POST.get('test1')
            t2_raw = request.POST.get('test2')
            t1 = float(t1_raw) if t1_raw else None
            t2 = float(t2_raw) if t2_raw else None

            if (t1 is not None and (t1 < 0 or t1 > 40)) or (t2 is not None and (t2 < 0 or t2 > 40)):
                error = "Marks must be between 0 and 40."
            else:
                s1 = round((t1 / 40) * 10, 2) if t1 is not None else None
                s2 = round((t2 / 40) * 10, 2) if t2 is not None else None
                total = round((s1 or 0) + (s2 or 0), 2)
                if total >= 16:
                    message = "Strong position. Keep this consistency going into the semester exam."
                elif total >= 10:
                    message = "You're in a fair spot — a bit more focus on the next test can push this higher."
                else:
                    message = "Low score isn't the end of the story — series tests are recoverable. Talk to your teacher, and focus hard on the semester exam prep."
                result = {'s1': s1, 's2': s2, 'total': total, 'message': message}
        except (ValueError, TypeError):
            error = "Enter valid numbers."
    return render(request, 'marks.html', {'result': result, 'error': error})


GRADE_TIERS = [
    ('S', 90), ('A+', 85), ('A', 80), ('B+', 75), ('B', 70),
    ('C+', 65), ('C', 60), ('D', 55), ('P (Pass)', 50),
]


def grade_calculator(request):
    count_visit(request, 'grade')
    subjects = []
    if request.method == 'POST':
        for i in range(1, 7):
            name = request.POST.get(f'subject{i}', '').strip()
            internal_raw = request.POST.get(f'internal{i}', '').strip()
            if not name or not internal_raw:
                continue
            try:
                internal = float(internal_raw)
            except ValueError:
                continue
            if internal < 0 or internal > 40:
                continue

            tiers = []
            for label, threshold in GRADE_TIERS:
                needed = max(24, threshold - internal)
                if needed > 60:
                    tiers.append({'label': label, 'needed': None})
                else:
                    tiers.append({'label': label, 'needed': round(needed, 1)})
            subjects.append({'name': name, 'internal': internal, 'tiers': tiers})
    return render(request, 'grade.html', {'subjects': subjects})


def stats(request):
    secret = os.environ.get('STATS_KEY')
    if not secret or request.GET.get('key') != secret:
        raise Http404()
    visits = PageVisit.objects.order_by('-count')
    return render(request, 'stats.html', {'visits': visits})