"""
Smart category prediction using simple keyword matching.
Designed so it can later be swapped for an NLP-based classifier
without changing the calling code (predict_category signature stays the same).
"""

CATEGORY_KEYWORDS = {
    'Travel': ['uber', 'ola', 'taxi', 'cab', 'bus', 'train', 'flight', 'fuel',
               'petrol', 'diesel', 'metro', 'parking', 'toll', 'auto'],
    'Food': ['pizza', 'burger', 'restaurant', 'zomato', 'swiggy', 'lunch',
             'dinner', 'breakfast', 'cafe', 'coffee', 'tea', 'snacks', 'food'],
    'Groceries': ['grocery', 'groceries', 'supermarket', 'vegetables',
                  'fruits', 'bigbasket', 'dmart', 'milk'],
    'Shopping': ['amazon', 'flipkart', 'myntra', 'mall', 'clothes',
                 'shoes', 'shopping', 'electronics'],
    'Bills': ['electricity', 'water bill', 'rent', 'wifi', 'internet',
              'recharge', 'phone bill', 'gas bill', 'emi', 'insurance'],
    'Entertainment': ['movie', 'netflix', 'spotify', 'concert', 'game',
                       'pvr', 'theatre', 'prime video', 'hotstar'],
    'Health': ['medicine', 'doctor', 'hospital', 'pharmacy', 'clinic',
               'gym', 'health', 'medical'],
    'Education': ['book', 'course', 'tuition', 'fees', 'college',
                  'udemy', 'exam', 'stationery'],
}


def predict_category(description: str) -> str:
    """Return the best-guess category for an expense description."""
    if not description:
        return 'Other'
    text = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return 'Other'
