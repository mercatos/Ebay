# --- Conditions ---
# New
# New other
# New with defects
# Certified - Refurbished
# Excellent - Refurbished
# Very Good - Refurbished
# Good - Refurbished
# Seller refurbished
# Like New
# Used
# Very Good
# Good
# Acceptable
# For parts or not working


def getConditionId(condition):
  conditions = {
    'New': '1000',
    'New other': '1500',
    'New with defects': '1750',
    'Certified - Refurbished': '2000',
    'Excellent - Refurbished': '2010',
    'Very Good - Refurbished': '2020',
    'Good - Refurbished': '2030',
    'Seller refurbished': '2500',
    'Like New': '2750',
    'Used': '3000',
    'Very Good': '4000',
    'Good': '5000',
    'Acceptable': '6000',
    'For parts or not working': '7000'
  }
  codes = []
  for con in condition.split("|"):
    codes.append(conditions[con])
  
  return "|".join(codes)