from django.shortcuts import render
from .forms import PickStockForm
from .graph_utils import create_graph_html

def home(request):

    if request.method == 'POST':
        form = PickStockForm(request.POST)
        if form.is_valid():
            stocks = form.cleaned_data['stocks']
            html =  create_graph_html(stocks)
            return render(request, 'stock_data_app/stock_data-graph.html', context={'form': form, 'graph': html})

    form = PickStockForm()
    return render(request, 'stock_data_app/stock_data-graph.html', context={'form': form})
