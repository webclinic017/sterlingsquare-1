from nsetools import Nse


class StockExchange:
    def nse_stock(self):
        nse = Nse()
        print("TOP GAINERS OF YESTERDAY")
        print(nse.get_top_gainers())
        print("###########################################")
        print("TOP LOSERS OF YESTERDAY")
        print(nse.get_top_losers())
        print("###########################################")
        print('-----------------------------------------------------'
              '--------------------------------------------------')


StockExchange_object = StockExchange()

if __name__ == "__main__":
    StockExchange_object.nse_stock()
