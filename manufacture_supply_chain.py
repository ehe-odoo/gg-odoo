import sys
"""
SPEC:
A product is consist of multiple components, each component is a product itself
There are 2 kinds of products:
1) stockable:
   a stockable product has 2 quantities: in stock qty; manufacture qty
   we will call stockable product Sx, like S1, S2...
2) consumable:
   a consumable is ALWAYS available
   we will call consumable product Cx, like C1, C2...

we want to calculate the manufacture qty for each product

Examples: (we always want to calculate the manufacture qty for S1)

A) S1 is made of S2, S2 is made of C1. We have 0 S2 on hand.
   How many manufacture qty do we have for S1? Answer: Infinite

        on hand     manufacture
   S1   0           Inf
   S2   0           Inf
   C1   Inf         Inf

B) S1 is made of S2, S2 is made of C1 + S3.

        on hand     manufacture
   S1   0           3
   S2   0           3
   C1   Inf         Inf
   S3   3           0

C) S1 = 4 * S2 + 3 * S3;
   S2 = 2 * S3

        on hand     manufacture
   S1   0           1
   S2   2           2
   S3   7           0

D) S1 is made of S2; S2 is made of S3

        on hand     manufacture
   S1   0           8
   S2   5           3
   S3   3           0
"""
class Product:
    def __init__(self, name, type='stock', on_hand=0.0):
        self.name = name
        self.type = type # str 'stock' or 'consumable'
        self.on_hand = on_hand # float
        self.manufacture_qty = 0.0 # float
        self.components = {} # key: [Product] component; value: [float] desired qty of each componet

    def __repr__(self):
        return '{} ({})'.format(self.name, self.on_hand)


# products_qty is a dictionary that holds all on hand qty of involved products
# not including the root
# [update] products_qty only includes restriction products
# if a component is made of consumable only or its children are made of consumable only
# we will not include it in the products_qty at all
def is_made_of_stockable(product):
    if product.type != 'stock':
        return False
    elif not product.components:
        return True
    else:
        return any([is_made_of_stockable(c) for c in product.components])

def get_products_qty(product):
    def get_products_qty_helper(product, dic):
        for component in product.components.keys():
            # we only care about products that have qty restrictions
            if is_made_of_stockable(component):
                dic[component] = component.on_hand
                get_products_qty_helper(component, dic)
    dic = {}
    get_products_qty_helper(product, dic)
    return dic

def can_make(product, n, products_qty):
    count = 0
    while count < n:
        # if there is no components at all, we can't make any
        if not product.components:
            return False
        next_layers = []
        # we only care about restriction components
        # if a component is a consumable or it is only made of consumable, it won't even show up in products_qty:
        restriction_components = [c for c in product.components if c in products_qty.keys()]
        for component in restriction_components:
            if products_qty[component] >= product.components[component]:
                # if we have enough on hand
                products_qty[component] -= product.components[component]
            else:
                # if there is possibility that it can be manufactured, then we calc this later
                next_layers.append((component, product.components[component] - products_qty[component]))
                products_qty[component] = 0.0

        # now it's time to calc the next layer if there is any
        for c, need_n in next_layers:
            if not can_make(c, need_n, products_qty):
                return False
        count += 1
    return True

def compute_manufacture_qty(product):
    if not is_made_of_stockable(product):
        return 'inf'
    products_qty = get_products_qty(product)
    count = 0
    while can_make(product, 1, products_qty):
        count += 1
        if count >= sys.maxsize:
            break
    return count

################################# TEST ######################################

import unittest

class TestBom(unittest.TestCase):

    # sanity
    # def test_sanity(self):
    #     self.assertEqual('foo'.upper(), 'FOO')

    # S1 = 4 * S2 + 3 * S3;
    # S2 = 2 * S3
    #
    #      on hand     manufacture
    # S1   0           1
    # S2   2           2
    # S3   7           0

    def test_nested(self):
        s3 = Product('s3', type='stock', on_hand=7.0)
        s2 = Product('s2', type='stock', on_hand=2.0)
        s2.components = {s3: 2.0}
        s1 = Product('s1', type='stock')
        s1.components = {s2: 4.0, s3: 3.0}
        s1.manufacture_qty = compute_manufacture_qty(s1)
        dic = get_products_qty(s1)
        self.assertDictEqual(dic, {s2: 2.0, s3: 7.0})
        self.assertEqual(s1.manufacture_qty, 1)

    # S1 is made of S2; S2 is made of S3
    #
    #      on hand     manufacture
    # S1   0           8
    # S2   5           3
    # S3   3           0
    def test_hierarchy(self):
        s3 = Product('s3', type='stock', on_hand=3.0)
        s2 = Product('s2', type='stock', on_hand=5.0)
        s2.components = {s3: 1.0}
        s1 = Product('s1', type='stock')
        s1.components = {s2: 1.0}
        s1.manufacture_qty = compute_manufacture_qty(s1)
        self.assertEqual(s1.manufacture_qty, 8)

    # s1 = 2 * s2 + 3 * s3 + 2 * s4;
    # s2 = 2 * s4 + 5 * c1
    # s3 = c1 + c2
    # s4 = s5 + 2 * c1
    #
    #      on hand     manufacture
    # s1   0           1
    # s2   1           1
    # s3   2           inf
    # s4   3           1
    # s5   1           0
    # c1   inf
    # c2   inf
    def test_combination(self):
        c1 = Product('c1', type='consumable')
        c2 = Product('c2', type='consumable')
        s1 = Product('s1')
        s2 = Product('s2', type='stock', on_hand=1.0)
        s3 = Product('s3', type='stock', on_hand=2.0)
        s4 = Product('s4', type='stock', on_hand=3.0)
        s5 = Product('s5', type='stock', on_hand=1.0)
        s1.components = {s2: 2.0, s3: 3.0, s4: 2.0}
        s2.components = {s4: 2.0, c1: 5.0}
        s3.components = {c1: 1.0, c2: 1.0}
        s4.components = {s5: 1.0, c1: 2.0}
        s1.manufacture_qty = compute_manufacture_qty(s1)
        self.assertEqual(s1.manufacture_qty, 1)

if __name__ == '__main__':
    unittest.main()
