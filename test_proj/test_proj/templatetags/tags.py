from django import template


def do_upper(parser, token):
    nodelist = parser.parse(('endblockupper', ))
    parser.delete_first_token()
    return UpperNode(nodelist)


class UpperNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        return output.upper()


register = template.Library()
register.tag('blockupper', do_upper)
