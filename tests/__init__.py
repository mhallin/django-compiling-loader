from django import template
from django.conf import settings
from django.template.defaulttags import register

settings.configure()


def do_upper(parser, token):
    nodelist = parser.parse(('endupper', ))
    parser.delete_first_token()
    return UpperNode(nodelist)


class UpperNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        return output.upper()


register.tag('blockupper', do_upper)
