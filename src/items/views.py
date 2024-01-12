from django.contrib.auth.decorators import login_required
from django.http import QueryDict
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse 
from projects import cache as projects_cache
from projects.decorators import project_required

from cfehome import http

from . import forms
from .models import Item

@project_required
@login_required
def item_list_view(request):
    object_list = Item.objects.filter(project=request.project)
    template_name = "items/list.html"
    if request.htmx:
        template_name = "items/snippets/table.html"
    return render(request, template_name, {'object_list': object_list})


@project_required
@login_required
def item_detail_inline_update_view(request, id=None):
    instance = get_object_or_404(Item, id=id, project=request.project)
    if not request.htmx:
        detail_url = instance.get_absolute_url()
        return redirect(detail_url)
    
    template_name = "items/snippets/table-row-edit.html"
    success_template = "items/snippets/table-row.html"
    if f"{request.method}".lower() == "patch":
        query_dict = QueryDict(request.body)
        data = query_dict.dict()
        form = forms.ItemPatchForm(data)
        if form.is_valid():
            valid_data = form.cleaned_data
            changed = False
            for k, v in valid_data.items():
                changed = True
                if v == "":
                    continue
                if not v:
                    continue
                setattr(instance, k , v)
            if changed:
                instance.save()
        template_name = success_template
        choices = Item.ItemStatus.choices
        context = {
            "instance": instance,
            "choices": choices,
            "form": form,
        }
        return render(request, template_name, context)
    
    form = forms.ItemInlineForm(request.POST or None, instance=instance)
    if form.is_valid():
        item_obj = form.save(commit=False)
        item_obj.last_modified_by = request.user 
        item_obj.save()
        template_name = success_template
    context = {
        "instance": instance,
        "form": form,
    }
    return render(request, template_name, context)


@project_required
@login_required
def item_detail_update_view(request, id=None):
    instance = get_object_or_404(Item, id=id, project=request.project)
    form = forms.ItemUpdateForm(request.POST or None, instance=instance)
    if form.is_valid():
        item_obj = form.save(commit=False)
        item_obj.last_modified_by = request.user 
        item_obj.save()
        return redirect(item_obj.get_absolute_url())
    context = {
        "instance": instance,
        "form": form,
    }
    return render(request, "items/detail.html", context)

@project_required
@login_required
def item_delete_view(request, id=None):
    instance = get_object_or_404(Item, id=id, project=request.project)
    if request.method == "POST":
        instance.delete()
        if request.htmx:
            return http.render_refresh_list_view(request)
        return redirect("items:list")
    return render(request, "items/delete.html", {"instance": instance})


@project_required
@login_required
def item_create_view(request):
    template_name = 'items/create.html'
    if request.htmx:
        template_name = 'items/snippets/form.html'
    form = forms.ItemCreateForm(request.POST or None)
    if form.is_valid():
        item_obj = form.save(commit=False)
        item_obj.project = request.project
        item_obj.added_by = request.user 
        item_obj.save()
        if request.htmx:
            return http.render_refresh_list_view(request)
        return redirect(item_obj.get_absolute_url())
    action_create_url = reverse("items:create")
    context = {
        "form": form,
        "btn_label": "Create item",
        "action_url": action_create_url
    }
    return render(request, template_name, context)