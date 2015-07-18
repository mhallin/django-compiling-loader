from django.template.base import TemplateDoesNotExist
from django.template.loader import find_template_loader, make_origin

from .compiler import compile_template


class Loader(object):
    is_usable = True

    def __init__(self, loaders):
        self._loaders = loaders
        self._cached_loaders = []

    @property
    def loaders(self):
        if not self._cached_loaders:
            self._cached_loaders = [
                find_template_loader(loader)
                for loader in self._loaders
            ]

        return self._cached_loaders

    def __call__(self, name, dirs=None):
        result = None
        template = None
        display_name = None

        for loader in self.loaders:
            try:
                template, display_name = loader(name, dirs)
            except TemplateDoesNotExist:
                pass
            else:
                result = (
                    template,
                    make_origin(display_name, loader, name, dirs))
                break

        if result is None:
            raise TemplateDoesNotExist(name)

        return compile_template(template), display_name

    def load_template_source(self, template_name, template_dirs=None):
        raise NotImplementedError('Can not implement this one...')
