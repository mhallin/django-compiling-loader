from django.views.generic import TemplateView


class LoopView(TemplateView):
    template_name = 'benchmark/loop.html'

    def get_context_data(self):
        data = super().get_context_data()

        data['data'] = [
            {'style': 'font-weight: bold', 'data': 'test data'},
            {'style': '', 'data': 'more data'},
            {'style': 'color: red', 'data': 'testing'},
            {'style': 'text-transform: uppercase'},
        ]

        return data
