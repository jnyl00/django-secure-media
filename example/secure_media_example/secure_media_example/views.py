from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.safestring import SafeString
from django.urls import reverse, reverse_lazy
from django.views.generic import View, TemplateView, FormView

from .forms import FileUploadForm


class CatalogView(TemplateView):
    """
    Catalog storage.
    """
    template_name = "catalog.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def _parse_storage(path):
            catalog = "<ul><li class='folder-symb'>{0}</li>{1}</ul>"
            curr_dirs, files = default_storage.listdir(path)

            # Files
            _contents = []
            for f in files:
                f_path = "/".join([path, f])
                _contents.append(
                    "<li>{0}&nbsp;{1}</li>".format(
                        "<a href=\"{0}\">{1}</a>".format(default_storage.url(f_path), f), 
                        (
                            "<a href=\"{0}\" class='badge rounded-pill bg-danger' title='Delete'><i class='bi bi-trash'></i></a>"
                        ).format(
                            reverse("file_delete", kwargs={"path_code": urlsafe_base64_encode(f_path.encode())})
                        ) if self.request.user.is_authenticated else ""
                    )
                )
            contents = "<ul>{0}</ul>".format("".join(_contents))

            # Get contents of sub-folders
            if curr_dirs:
                for _dir in curr_dirs:
                    contents += _parse_storage("/".join([path, _dir]))
            return catalog.format(path, contents)

        try:
            context["catalog"] = SafeString(_parse_storage("."))
        except FileNotFoundError:
            context["catalog"] = SafeString("<ul></ul>")
        return context


class UploadFileView(FormView):
    """
    Upload file.
    """
    form_class = FileUploadForm
    template_name = "upload.html"
    success_url = reverse_lazy("catalog")

    def form_valid(self, form):
        folder = form.cleaned_data['upload_to']
        file = form.cleaned_data['file']
        default_storage.save("{0}/{1}".format(folder, file.name), file)
        return super().form_valid(form)


class DeleteFileView(View):
    """
    Delete file.
    """
    def get(self, request, *args, **kwargs):
        path_code = kwargs.get("path_code", "")
        path = urlsafe_base64_decode(path_code).decode()
        default_storage.delete(path)
        return HttpResponseRedirect(reverse("catalog"))
