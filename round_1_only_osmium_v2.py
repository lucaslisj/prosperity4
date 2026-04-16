from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import json

class Trader:
    
    # --- CONFIG ---
    ROOT_FAIR = 10000
    OSMIUM_WINDOW = 10
    SKEW_FACTOR = 4

    def run(self, state: TradingState):
        """Called every tick. Returns orders, conversions, and persistent data."""

        result = {}
        last_prices = json.loads(state.traderData) if state.traderData else []

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 0

            # ========================================================== #
            #                         PEPPER ROOT                        #
            # ========================================================== #
            if product == "INTARIAN_PEPPER_ROOT": #temporary hold
                pass
                # position = state.position.get(product,0)
                # limit = 80

                                
                # #take good offers on the market

                # for ask_price, ask_amount in sorted(order_depth.sell_orders.items()):
                #     if ask_price < 10000:
                #         max_buy = limit - position
                #         qty = min(-ask_amount,max_buy)
                #         if qty > 0:
                #             orders.append(Order(product, ask_price, qty))
                #             position += qty  # track it
                #     else:
                #         break
                
                # for bid_price, bid_amount in sorted(order_depth.buy_orders.items(),reverse=True):
                #     if bid_price > 10000:
                #         max_sell = limit + position
                #         qty = min(bid_amount,max_sell)
                #         if qty > 0:
                #             orders.append(Order(product, bid_price, -qty))
                #             position -= qty  # track it
                #     else:
                #         break
            
                # buy_qty = limit - position
                # sell_qty = limit + position


                # #place my orders in the book
                # if buy_qty > 0:
                #     orders.append(Order(product,9993,buy_qty))
                # if sell_qty > 0:
                #     orders.append(Order(product,10007,-sell_qty))
            
                # result[product] = orders
                # continue
            # ========================================================== #
            #                         OSMIUM                             #
            # ========================================================== #
            elif product == "ASH_COATED_OSMIUM":
                position = state.position.get(product,0)
                limit = 80
                inventory_ratio = position / limit
                skew = inventory_ratio * self.SKEW_FACTOR

                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())
                mid_price = (best_bid + best_ask) / 2

                last_prices.append(mid_price)
                if len(last_prices) > self.OSMIUM_WINDOW:
                    last_prices.pop(0)

                #calculate acceptable price based on avg of last 10 ticks
                acceptable_price = sum(last_prices) / len(last_prices)
                adjusted_price = acceptable_price - skew

                #take good prices on the market
                for ask_price, ask_amount in sorted(order_depth.sell_orders.items()):
                    if ask_price < adjusted_price:
                        max_buy = limit - position
                        qty = min(-ask_amount,max_buy)
                        if qty > 0:
                            orders.append(Order(product, ask_price, qty))
                            position += qty
                    else:
                        break

                for bid_price, bid_amount in sorted(order_depth.buy_orders.items(),reverse = True):
                    if bid_price > adjusted_price:
                        max_sell = limit + position
                        qty = min(bid_amount, max_sell)
                        if qty > 0:
                            orders.append(Order(product, bid_price, -qty))
                            position -= qty
                    else:
                        break
                
                # quote my orders dynamically
                
                market_bid = max(order_depth.buy_orders.keys()) 
                market_ask = min(order_depth.sell_orders.keys())
                
                quote_bid = market_bid + 1 - int(skew)
                quote_ask = market_ask - 1 - int(skew)

                remaining_buy = limit - position
                remaining_sell = limit + position

                if remaining_buy > 0:
                    orders.append(Order(product, quote_bid, remaining_buy))
                if remaining_sell > 0:
                    orders.append(Order(product, quote_ask, -remaining_sell))

                result[product] = orders

        traderData = json.dumps(last_prices)
        return result, 0, traderData