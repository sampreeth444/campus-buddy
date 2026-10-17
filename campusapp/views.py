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


MAX_ROWS = 8
START_ROWS = 3
GRADE_START_ROWS = 2


def attendance_level(attended, total):
    """Where a student stands, using whole-number math.
    full = 85% or more (5 attendance marks), ok = 75% to 85%, low = below 75%.
    spare = classes they can still miss and stay at 85%.
    need = classes to attend in a row to get back to the next limit."""
    if 20 * attended >= 17 * total:
        return {'level': 'full', 'spare': (20 * attended - 17 * total) // 17, 'need': 0}
    if 4 * attended >= 3 * total:
        return {'level': 'ok', 'spare': 0, 'need': -(-(17 * total - 20 * attended) // 3)}
    return {'level': 'low', 'spare': 0, 'need': 3 * total - 4 * attended}


def attendance_calculator(request):
    count_visit(request, 'attendance')
    posted = request.method == 'POST'
    mode = request.POST.get('mode') if posted else request.GET.get('mode')
    mode = 'all' if mode == 'all' else 'one'
    row_count = MAX_ROWS if mode == 'all' else 1

    rows = []
    results = []
    errors = []
    highest = 0

    for i in range(1, row_count + 1):
        row = {
            'i': i,
            'name': request.POST.get(f'subject{i}', '').strip() if posted else '',
            'total': request.POST.get(f'total{i}', '').strip() if posted else '',
            'attended': request.POST.get(f'attended{i}', '').strip() if posted else '',
            'skip': request.POST.get(f'skip{i}', '').strip() if posted else '',
        }
        rows.append(row)
        if row['name'] or row['total'] or row['attended'] or row['skip']:
            highest = i

        if not posted or (not row['total'] and not row['attended']):
            continue

        label = (row['name'] or f'Subject {i}') if mode == 'all' else 'Your attendance'

        def add_error(message):
            errors.append(f"{label}: {message}" if mode == 'all' else message)

        try:
            total = int(row['total'])
            attended = int(row['attended'])
            skip = int(row['skip'] or 0)
        except ValueError:
            add_error("enter whole numbers for total held and attended.")
            continue

        if total <= 0 or attended < 0 or skip < 0 or attended > total:
            add_error("attended can't be more than total held.")
            continue

        now = attendance_level(attended, total)
        after = attendance_level(attended, total + skip) if skip > 0 else now

        results.append({
            'name': label,
            'now_pct': round(attended / total * 100, 2),
            'now_level': now['level'],
            'has_leave': skip > 0,
            'new_pct': round(attended / (total + skip) * 100, 2) if skip > 0 else None,
            'new_level': after['level'],
            'level': after['level'],
            'spare': after['spare'],
            'need': after['need'],
        })

    visible = max(START_ROWS, highest)
    for row in rows:
        row['show'] = row['i'] <= visible

    return render(request, 'attendance.html', {
        'mode': mode,
        'rows': rows,
        'results': results,
        'errors': errors,
    })


def marks_calculator(request):
    count_visit(request, 'marks')
    posted = request.method == 'POST'
    mode = request.POST.get('mode') if posted else request.GET.get('mode')
    mode = 'all' if mode == 'all' else 'one'
    row_count = MAX_ROWS if mode == 'all' else 1

    rows = []
    results = []
    errors = []
    highest = 0

    for i in range(1, row_count + 1):
        row = {
            'i': i,
            'name': request.POST.get(f'subject{i}', '').strip() if posted else '',
            'test1': request.POST.get(f'test1_{i}', '').strip() if posted else '',
            'test2': request.POST.get(f'test2_{i}', '').strip() if posted else '',
        }
        rows.append(row)
        if row['name'] or row['test1'] or row['test2']:
            highest = i

        if not posted or (not row['test1'] and not row['test2']):
            continue

        label = (row['name'] or f'Subject {i}') if mode == 'all' else 'Your marks'

        def add_error(message):
            errors.append(f"{label}: {message}" if mode == 'all' else message)

        try:
            t1 = float(row['test1']) if row['test1'] else None
            t2 = float(row['test2']) if row['test2'] else None
        except ValueError:
            add_error("enter valid numbers.")
            continue

        if (t1 is not None and not 0 <= t1 <= 40) or (t2 is not None and not 0 <= t2 <= 40):
            add_error("marks must be between 0 and 40.")
            continue

        s1 = round(t1 / 40 * 10, 2) if t1 is not None else None
        s2 = round(t2 / 40 * 10, 2) if t2 is not None else None
        total = round((s1 or 0) + (s2 or 0), 2)

        if total >= 16:
            message = "Strong position. Keep this consistency going into the semester exam."
        elif total >= 10:
            message = "You're in a fair spot — a bit more focus on the next test can push this higher."
        else:
            message = "Low score isn't the end of the story — series tests are recoverable. Talk to your teacher, and focus hard on the semester exam prep."

        results.append({'name': label, 's1': s1, 's2': s2, 'total': total, 'message': message})

    visible = max(START_ROWS, highest)
    for row in rows:
        row['show'] = row['i'] <= visible

    return render(request, 'marks.html', {
        'mode': mode,
        'rows': rows,
        'results': results,
        'errors': errors,
    })


GRADE_TIERS = [
    ('S', 90), ('A+', 85), ('A', 80), ('B+', 75), ('B', 70),
    ('C+', 65), ('C', 60), ('D', 55), ('P (Pass)', 50),
]


def grade_calculator(request):
    count_visit(request, 'grade')
    posted = request.method == 'POST'
    rows = []
    subjects = []
    errors = []
    highest = 0

    for i in range(1, MAX_ROWS + 1):
        row = {
            'i': i,
            'name': request.POST.get(f'subject{i}', '').strip() if posted else '',
            'internal': request.POST.get(f'internal{i}', '').strip() if posted else '',
        }
        rows.append(row)
        if row['name'] or row['internal']:
            highest = i

        if not posted or not row['internal']:
            continue

        label = row['name'] or f'Subject {i}'
        try:
            internal = float(row['internal'])
        except ValueError:
            errors.append(f"{label}: enter a valid internal mark.")
            continue

        if not 0 <= internal <= 40:
            errors.append(f"{label}: internal mark must be between 0 and 40.")
            continue

        tiers = []
        for tier_label, threshold in GRADE_TIERS:
            needed = max(24, threshold - internal)
            if needed > 60:
                tiers.append({'label': tier_label, 'needed': None})
            else:
                tiers.append({'label': tier_label, 'needed': round(needed, 1)})
        subjects.append({'name': label, 'internal': internal, 'tiers': tiers})

    visible = max(GRADE_START_ROWS, highest)
    for row in rows:
        row['show'] = row['i'] <= visible

    return render(request, 'grade.html', {
        'rows': rows,
        'subjects': subjects,
        'errors': errors,
    })


def stats(request):
    secret = os.environ.get('STATS_KEY')
    if not secret or request.GET.get('key') != secret:
        raise Http404()
    visits = PageVisit.objects.order_by('-count')
    return render(request, 'stats.html', {'visits': visits})