from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from config_template.models import *
from config_template.utils import *
import json
import traceback
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied

# Create your views here.
@login_required
@permission_required('config_template.add_template', raise_exception=True)
def new_template(request):
    return render(request, 'config_template/new_template.html')

@login_required
@csrf_exempt
@permission_required('config_template.add_template', raise_exception=True)
def ajax_new_template(request):
    try:
        template = Template()
        template.name = request.POST.get('name')
        template.type = request.POST.get('type')
        template.content = request.POST.get('content')
        template.save()
        post_params = json.loads(request.POST.get('params'))

        for post_param in post_params:
            param = Param()
            param.template = template
            param.name = post_param['param_name']
            param.type = post_param['param_type']
            param.default = post_param['param_default']
            param.save()
        return HttpResponse("Add new template success")
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        return HttpResponse("Add new template failed")

@csrf_exempt
@login_required
@permission_required('config_template.change_template', raise_exception=True)
def ajax_edit_template(request):
    try:
        template = Template.objects.get(pk=request.POST.get("id"))
        template.name = request.POST.get('name')
        template.type = request.POST.get('type')
        template.content = request.POST.get('content')
        template.save()
        post_params = json.loads(request.POST.get('params'))
        # Update or insert param
        current_params_name = []
        for post_param in post_params:
            current_params_name.append(post_param['param_name'])
            param = None
            try:
                param = Param.objects.get(name=post_param['param_name'], template=template)
            except Param.DoesNotExist as e:
                param = Param()
            param.template = template
            param.name = post_param['param_name']
            param.type = post_param['param_type']
            param.default = post_param['param_default']
            param.save()
        # Remove param
        params = template.param_set.all()
        for param in params:
            if (param.name not in current_params_name):
                param.delete()
        return HttpResponse("Edit template success")
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        return HttpResponse("Edit template failed")

@login_required
def list_template(request):
    templates = Template.objects.order_by('type', 'name')
    data = {}
    data['templates'] = templates
    return render(request, 'config_template/list_template.html',data)

@login_required
@permission_required('config_template.change_template', raise_exception=True)
def edit_template(request, template_id):
    template = Template.objects.get(pk=template_id)
    template.content = template.content.replace("\n", "\\n")
    template.params = template.param_set.order_by('id')
    data = {}
    data['template'] = template
    return render(request, 'config_template/edit_template.html',data)

@login_required
@permission_required('config_template.delete_template', raise_exception=True)
def delete_template(request, template_id):
    template = Template.objects.get(pk=template_id)
    template.delete()
    return redirect('/config-template/list-template')
