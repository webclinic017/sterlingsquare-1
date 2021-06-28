from django import template
from accounts.models import StockHistory, StockNames
from accounts.views import num_quantize
from yahoo_fin import stock_info as si
from utils.util_functions import parse_tick_data
from sterling_square.TickerSingleton import Singleton2

register = template.Library()


@register.simple_tag
def get_type_text(order_type):
    print("order_type    ", order_type)
    value = ""
    if str(order_type) == "limit_order":
        value = "limit buy"
    elif str(order_type) == "market_order":
        value = "market order"
    return value


@register.simple_tag
def get_stock_price(symbol):
    try:
        s = Singleton2.get_instance("2")
        stock = StockNames.objects.filter(symbol=symbol).first()
        price = parse_tick_data(s.tick_data, int(stock.token))[0]
        if not price:
            price = si.get_live_price(symbol + ".NS")
        return "₹{0:,.2f}".format(num_quantize(price))
    except Exception as e:
        print("34", e)
        return None


@register.simple_tag
def get_stock_name(symbol):
    try:
        stock = StockNames.objects.filter(symbol=symbol).first()
        return stock.name
        # stock_data_json = StockHistory.objects.get(
        #     stock__symbol=symbol).history_json.get("data")
        # return stock_data_json.get("stockname")
    except:
        return None


@register.simple_tag
def check_pos_or_neg(pos_obj):
    if pos_obj.gl_history_position_rel.all():
        gainloss = pos_obj.gl_history_position_rel.all()[0].unrealised_gainloss
    else:
        gainloss = 0.00
    # if float(value) > 0:
    #     value = "+"+value
    # else:
    #     value = "-" + value
    return gainloss


@register.simple_tag
def get_amount(price, share_num):
    if price and share_num:
        price = price.replace(",", "").replace("₹", "")
        return "₹{0:,.2f}".format(num_quantize(float(price) * int(share_num)))
    else:
        return price


@register.simple_tag
def format_currency(price):
    price = num_quantize(float(price))
    return "₹{0:,.2f}".format(price)
