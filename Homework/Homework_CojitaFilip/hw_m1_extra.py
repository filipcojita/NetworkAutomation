def find_best_shop(cart, shops):
    best_shop = None
    min_cost = float('inf')

    for shop_name, shop_items in shops.items():
        total_cost = 0
        for item, quantity in cart.items():
            if item not in shop_items:
                total_cost = float('inf')  # Exclude shop if an item is missing
                break
            total_cost += shop_items[item] * quantity

        if total_cost < min_cost:
            min_cost = total_cost
            best_shop = shop_name

    return {best_shop: min_cost} if best_shop else {}

cart = {'mar': 10, 'prune': 15, 'banane': 5, 'portocale':3}

shop_K = {'mar': 1.2, 'prune': 4, 'banane': 5.5, 'portocale': 2, 'castraveti':7}
shop_P = {'mar': 1.3, 'prune': 3, 'banane': 8,'ciocolata':20}
shop_L = {'mar': 1.4, 'prune': 2, 'banane': 10,'pasta de dinti':39, 'portocale':4}
shop_M = {'mar': 1.5, 'prune': 1, 'banane': 12, 'deodorant':21}

shops = {'profi': shop_P, 'lidl': shop_L, 'kaufland': shop_K, 'mega':shop_M}

result = find_best_shop(cart, shops)
print(result)
