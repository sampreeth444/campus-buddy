from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def attendance_calculator(request):
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

def help_page(request):
    return render(request, 'help.html')

def marks_calculator(request):
    result = None
    if request.method == 'POST':
        t1_raw = request.POST.get('test1')
        t2_raw = request.POST.get('test2')

        s1 = round((float(t1_raw) / 40) * 10, 2) if t1_raw else None
        s2 = round((float(t2_raw) / 40) * 10, 2) if t2_raw else None
        total = round((s1 or 0) + (s2 or 0), 2)

        if total >= 16:
            message = "Strong position. Keep this consistency going into the semester exam."
        elif total >= 10:
            message = "You're in a fair spot — a bit more focus on the next test can push this higher."
        else:
            message = "Low score isn't the end of the story — series tests are recoverable. Talk to your teacher about improvement options, and focus hard on the semester exam prep."

        result = {'s1': s1, 's2': s2, 'total': total, 'message': message}
    return render(request, 'marks.html', {'result': result})