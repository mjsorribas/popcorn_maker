from django.conf import settings
from django.db.models import Q
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, Http404, HttpResponseForbidden

from django_extensions.db.fields import json
from ..decorators import valid_user_project
from ..forms import ProjectForm
from ..models import Project
from ..templates import export_template
from ...base.decorators import json_handler, login_required_ajax


@require_GET
@login_required_ajax
def project_list(request):
    """List projects saved that belong to the authed user."""
    queryset = Project.objects.filter(~Q(status=Project.REMOVED),
                                      author=request.user)
    response = {
        'error': 'okay',
        'projects': [{'name': p.name, 'id': p.uuid} for p in queryset],
        }
    return HttpResponse(json.dumps(response), mimetype='application/json')


def get_project_data(cleaned_data):
    template = cleaned_data['template']
    metadata = cleaned_data['data']
    return {
        'name': cleaned_data['name'],
        'metadata': metadata,
        'template': template,
        }


@require_POST
@json_handler
@login_required_ajax
def project_add(request):
    """Saves the metadata of a user's Project"""
    form = ProjectForm(request.JSON)
    if form.is_valid():
        data = get_project_data(form.cleaned_data)
        data['author'] = request.user
        project = Project.objects.create(**data)
        response = {
            'error': 'okay',
            'project': project.butter_data,
            'url': project.get_absolute_url(),
            }
    else:
        response = {
            'error': 'error',
            'form_errors': form.errors
            }
    return HttpResponse(json.dumps(response), mimetype='application/json')


@json_handler
@login_required_ajax
@valid_user_project(['uuid'])
def project_detail(request, project):
    """Returns and saves an specific ``Project``."""
    if request.method == 'POST' and request.JSON:
        if project.author != request.user:
            if project.is_forkable:
                project = Project.objects.fork(project, request.user)
            else:
                return HttpResponseForbidden()
        form = ProjectForm(request.JSON)
        if form.is_valid():
            project.name = form.cleaned_data['name']
            project.metadata = form.cleaned_data['data']
            project.save()
            response = {
                'error': 'okay',
                'project': project.butter_data,
                'url': project.get_project_url(),
                }
        else:
            response = {
                'error': 'error',
                'form_errors': form.errors
                }
        return HttpResponse(json.dumps(response), mimetype='application/json')
    response = {
        'error': 'okay',
        # Butter needs the project metadata as a string that can be
        # parsed to JSON
        'url': project.get_project_url(),
        'project': project.metadata,
        }
    return HttpResponse(json.dumps(response), mimetype='application/json')


@require_POST
@json_handler
@login_required_ajax
def project_publish(request, uuid):
    """Publish the selected project and makes available in the
    community gallery."""
    if request.method == 'POST':
        try:
            project = Project.objects.get(~Q(status=Project.REMOVED),
                                          uuid=uuid, author=request.user)
        except Project.DoesNotExist:
            return HttpResponseForbidden()
        project.is_shared = True
        response = {
            'error': 'okay',
            'url': '%s%s' % (settings.SITE_URL, project.get_project_url()),
            }
        return HttpResponse(json.dumps(response), mimetype='application/json')
    raise Http404


@login_required_ajax
def user_details(request):
    response = {
        'name': request.user.profile.display_name,
        'username': request.user.username,
        'email': request.user.email,
        }
    return HttpResponse(json.dumps(response), mimetype='application/json')
