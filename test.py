import unittest
from ob_aggregator import calculate_price_inorder as algo
from decimal import Decimal

ONE = Decimal(1)
TWO = Decimal(2)
THREE = Decimal(3)
FIVE = Decimal(5)
SIX = Decimal(6)
TEN = Decimal(10)
DATA_ONES = [[ONE, ONE]] * 5
DATA_ASC = [[ONE, ONE], [TWO, TWO], [THREE, THREE]]

class AlgoTests(unittest.TestCase):

    def test_ones(self):
        self.assertEqual(ONE, algo(DATA_ONES, ONE))
        self.assertEqual(TWO, algo(DATA_ONES, TWO))
        self.assertEqual(THREE, algo(DATA_ONES, THREE))
        self.assertEqual(FIVE, algo(DATA_ONES, FIVE))
        self.assertRaises(Exception, algo, DATA_ONES, SIX)
        self.assertRaises(Exception, algo, DATA_ONES, TEN)

    def test_fractional(self):
        self.assertEqual(Decimal('0.01'), algo(DATA_ASC, Decimal('0.01')))
        self.assertEqual(Decimal('3.02'), algo(DATA_ASC, Decimal('2.01')))
        self.assertEqual(Decimal('9.5'), algo(DATA_ASC, Decimal('4.5')))
        self.assertEqual(Decimal('14'), algo(DATA_ASC, Decimal('6')))
        self.assertRaises(Exception, algo, DATA_ASC, Decimal('6.00000000000000000000000000001'))
        self.assertRaises(Exception, algo, DATA_ASC, TEN)

if __name__ == "__main__":
    unittest.main()