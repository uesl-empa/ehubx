"""Common model functionality"""


def calculate_crf(interest_rate: float, num_years: int):
    """
    Calculates the Capital Recovery Factor (CRF) for investments

    :param interest_rate: Interest rate
    :type interest_rate: float
    :param num_years: Number of annuity years
    :type num_years: int
    :return: CRF
    :rtype: _type_
    """
    crf = (interest_rate * (1 + interest_rate) ** num_years
           / ((1 + interest_rate) ** (num_years - 1)))
    return crf
