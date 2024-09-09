import json
from math import trunc
from urllib.parse import unquote

from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.http import HttpResponse, Http404
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404, render
from django.template import loader

from .forms import ThreadForm
from .models import Category, Thread, Subcategory


def dashboard(request):
    thread_fields = ['id', 'subject', 'subcategory__name']
    latest_threads = Thread.objects.get_latest(thread_fields)

    recent_updates = [dict(zip(thread_fields, thread)) for thread in latest_threads]

    context = {
        'recent_updates': recent_updates
    }
    template = loader.get_template('dashboard.html')
    return HttpResponse(template.render(context, request))


def subcategory(request, name):
    name_unquote = unquote(name)
    subcat = Subcategory.get_by_name(name_unquote)

    if not subcat:
        raise Http404("No Subcategory found with name " + name)

    if subcat.category.auth_required and not request.user.is_authenticated:
        page = 'login'
        next_page = request.path
        return redirect(f'{page}?next={next_page}')

    threads = Thread.objects.get_subcategory_latest(subcat.id)

    form = ThreadForm()
    if request.user.is_authenticated:
        form.fields['author_name'].initial = request.user.username
        form.fields['author_email'].initial = request.user.email

    context = {
        'subcategory': subcat,
        'threads': threads,
        'form': form
    }
    template = loader.get_template('subcategory.html')
    return HttpResponse(template.render(context, request))


def thread_create(request, subcategory_name):
    subcat = Subcategory.get_by_name(subcategory_name)

    form = ThreadForm(request.POST, request.FILES)
    if form.is_valid():
        thread_instance = form.instance
        if request.user.is_authenticated:
            thread_instance.author_name = request.user.username
            thread_instance.author_email = request.user.email
        thread_instance.save()
        return redirect('subcategory', name=subcategory_name)
    else:
        threads = Thread.objects.get_subcategory_latest(subcat.id)
        context = {
            'subcategory': subcat,
            'threads': threads,
            'form': form
        }

        return render(request, 'subcategory.html', context)


def thread_view(request, id):
    thread = get_object_or_404(Thread, id=id)

    form = ThreadForm()
    form.fields['subject'].initial = thread.subject

    if request.user.is_authenticated:
        form.fields['author_name'].initial = request.user.username
        form.fields['author_email'].initial = request.user.email

    context = {
        'thread': thread,
        'form': form
    }
    template = loader.get_template('thread.html')
    return HttpResponse(template.render(context, request))


def thread_reply(request, root_id):
    form = ThreadForm(request.POST, request.FILES)
    if form.is_valid():
        thread_instance = form.instance
        thread_instance.root_thread_id = root_id
        if request.user.is_authenticated:
            thread_instance.author_name = request.user.username
            thread_instance.author_email = request.user.email

        thread_instance.save()
        Thread.objects.update_date(root_id)
        return redirect('thread_view', id=root_id)
    else:
        thread = get_object_or_404(Thread, id=root_id)
        context = {
            'thread': thread,
            'form': form
        }

        return render(request, 'thread.html', context)


class LoginUser(auth_views.LoginView):
    template_name = 'login.html'


def logout_user(request):
    logout(request)
    return redirect('home')


def thread_get_updated_date(request, thread_id):
    thread = Thread.objects.get_by_id(thread_id)
    response = trunc(thread.updated_date.timestamp())
    return HttpResponse(response)


def thread_edit_message(request, thread_id):
    is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax_request and request.method == 'POST':
        data = json.load(request)
        new_message = data.get('newMessage')
        reply_id = data.get('replyId')
        update_thread_id = reply_id if reply_id else thread_id

        Thread.objects.update_message(update_thread_id, new_message)
        if reply_id:
            Thread.objects.update_date(thread_id)

        return HttpResponse(status=204)

    return HttpResponseBadRequest()


def set_categories(request):
    return {'categories': Category.get_all()}
