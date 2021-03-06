from django.shortcuts import render
from watcher.utils import *
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from config_template.models import *
import traceback
import time
import watcher.models as models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied

# Create your views here.
@csrf_exempt
@login_required
@permission_required('watcher.add_watcher', raise_exception=True)
def new_watcher(request):
    data = {}
    if request.method == 'POST':
        watcher_name = request.POST.get("watcher_name")
        data['msg'] = "Post"
        post_params = {}
        for key in request.POST:
            if key.startswith("filehidden"):
                fkey = key[11:]
                if(request.FILES.get(fkey, None)):
                    post_file = request.FILES[fkey]
                    file_content=""
                    for chunk in post_file.chunks():
                        file_content += chunk.decode("utf8")
                    post_params[fkey] = convert(file_content)
                else:
                    post_params[fkey] = request.POST[key]
            else:
                post_params[key] = request.POST[key]

        template = Template.objects.get(pk=post_params['template_id'])
        content = template.content%post_params
        data['content'] = content
        try:
            watcher_thread = create_new_watcher(content, watcher_name)
            watcher_thread.start()
            data['result'] = "Success"
        except Exception as e:
            data['result'] = str(e)
            traceback.print_exc()


    templates = Template.objects.filter(type="watcher").order_by('name').all()
    for template in templates:
        template.params = template.param_set.order_by('id')

    data['templates'] = templates
    return render(request, 'watcher/new_watcher.html', data)

@csrf_exempt
@login_required
@permission_required('watcher.can_run', raise_exception=True)
def watcher_action(request):
    try:
        if request.method == 'POST':
            action = request.POST.get('action', None)
            watcher_name = request.POST.get('name', None)
            watcher_model = models.Watcher.objects.get(name=watcher_name)
            if action == 'destroy':
                watcher_model.delete()
                del settings.WATCHER_THREADS[watcher_name]
            elif action == 'start':
                old_watcher = settings.WATCHER_THREADS[watcher_name]
                watcher_obj = old_watcher.watcher
                watcher_obj.set_running(True)
                new_watcher = WatcherThread(old_watcher.getName(), watcher_obj)
                del old_watcher
                settings.WATCHER_THREADS[watcher_name] = new_watcher
                watcher_model.status = '1'
                new_watcher.start()
            elif action == 'stop':
                 settings.WATCHER_THREADS[watcher_name].stop()
                 watcher_model.status = '0'
            elif action == 'restart':
                 settings.WATCHER_THREADS[watcher_name].stop()
                 watcher_model.status = '0'
                 time.sleep(3)
                 old_watcher = settings.WATCHER_THREADS[watcher_name]
                 watcher_obj = old_watcher.watcher
                 watcher_obj.set_running(True)
                 new_watcher = WatcherThread(old_watcher.getName(), watcher_obj)
                 del old_watcher
                 old_watcher = settings.WATCHER_THREADS[watcher_name]
                 watcher_obj = old_watcher.watcher
                 watcher_obj.set_running(True)
                 new_watcher = WatcherThread(old_watcher.getName(), watcher_obj)
                 del old_watcher
                 settings.WATCHER_THREADS[watcher_name] = new_watcher
                 watcher_model.status = '1'
                 new_watcher.start()

            result = '{"status":"success", "msg": "%(action)s success"}'%{"action":action}
    except Exception as e:
        result = '{"status":"error", "msg": "%(action)s fail: %(error)s" }'%{"action":action, "error": str(e)}
        traceback.print_exc()
    return HttpResponse(result)

@login_required
def list_watcher(request):
    watcher_threads = models.Watcher.objects.all()
    for watcher_thread in watcher_threads:
        if settings.WATCHER_THREADS.get(watcher_thread.name, None):
            watcher_thread.is_alive = settings.WATCHER_THREADS.get(watcher_thread.name).is_alive()
        else:
            watcher_thread.is_alive = False
    data = {'watcher_threads': watcher_threads}

    return render(request, 'watcher/list_watcher.html', data)

@login_required
def ajax_list_watcher(request):
    watcher_threads = models.Watcher.objects.all()
    for watcher_thread in watcher_threads:
        if settings.WATCHER_THREADS.get(watcher_thread.name, None):
            watcher_thread.is_alive = settings.WATCHER_THREADS.get(watcher_thread.name).is_alive()
        else:
            watcher_thread.is_alive = False
    data = {'watcher_threads': watcher_threads}
    return render(request, 'watcher/ajax_list_watcher.html', data)

@login_required
def ajax_notifications(request):
    notifs = models.Notification.objects.filter(status='0').order_by('-created_at')[:5]
    total = models.Notification.objects.filter(status='0').count()
    data = {}
    data['notifs'] = notifs
    data['total'] = total
    return render(request, 'watcher/ajax_notifycations.html', data)

@login_required
def list_notifications(request):

    notifs_list = models.Notification.objects.order_by('-created_at')
    total = models.Notification.objects.filter(status='0').count()
    paginator = Paginator(notifs_list, 5)
    page = request.GET.get('page', 1)
    try:
        notifs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        notifs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        notifs = paginator.page(paginator.num_pages)
    data = {}
    data['page'] = page
    data['notifs'] = notifs
    return render(request, 'watcher/list_notifycations.html', data)

@login_required
def ajax_list_notifications(request):

    notifs_list = models.Notification.objects.order_by('-created_at')
    total = models.Notification.objects.filter(status='0').count()
    paginator = Paginator(notifs_list, 5)
    page = request.GET.get('page', 1)
    try:
        notifs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        notifs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        notifs = paginator.page(paginator.num_pages)
    data = {}
    data['notifs'] = notifs
    return render(request, 'watcher/ajax_list_notifycations.html', data)

@csrf_exempt
@login_required
def notify_action(request):
    try:
        if request.method == 'POST':
            action = request.POST.get('action', None)
            notif_id = request.POST.get('id', None)
            if action == "status1":
                notif = models.Notification.objects.get(pk=notif_id)
                notif.status = "1"
                notif.save()
            elif action == "status0":
                notif = models.Notification.objects.get(pk=notif_id)
                notif.status = "0"
                notif.save()
            elif action == "readall":
                notifs = models.Notification.objects.all()
                for notif in notifs:
                    notif.status = "1"
                    notif.save()
            elif action == "delall":
                notifs = models.Notification.objects.all()
                for notif in notifs:
                    notif.delete()
            elif action == "delete":
                notif = models.Notification.objects.get(pk=notif_id)
                notif.delete()
            else:
                pass
            return HttpResponse("success")
    except Exception as e:
        return HttpResponse("error")
