from django.shortcuts import render

def create_feedback(request):
    return render(request, 'feedback/create.html')

def list_feedback(request):
    return render(request, 'feedback/list.html')

def admin_feedback(request):
    feedbacks = []
    return render(request, 'feedback/admin.html', {'feedbacks': feedbacks})
