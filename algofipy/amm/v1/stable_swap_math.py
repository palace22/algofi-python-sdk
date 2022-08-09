
# IMPORTS

# external
from typing import List, Tuple

# local

# constants
A_PRECISION = 1000000

def get_D(token_amounts: List[int], amplification_factor: int) -> Tuple[int, int]:
    """Calculate the D quantity in the stableswap invariant given a list of token amounts and an amplication factor.

    :param token_amounts: list of token amounts in pool
    :type token_amounts: list of ints
    :param amplication_factor: quantity of sensitivity to price change
    :type amplication_factor: int
    :return: D quantity
    :rtype: (int, int)
    """
    N_COINS = len(token_amounts)
    S = 0
    Dprev = 0

    for _x in token_amounts:
        S += _x
    if S == 0:
        return 0

    D = S
    Ann = amplification_factor * (N_COINS ** N_COINS)
    for _i in range(255):
        D_P = D
        for _x in token_amounts:
            D_P = int(
                D_P * D // (_x * N_COINS)
            )
        Dprev = D
        D = (
            (Ann * S // A_PRECISION + D_P * N_COINS)
            * D
            // ((Ann - A_PRECISION) * D // A_PRECISION + (N_COINS + 1) * D_P)
        )
        if D > Dprev:
            if D - Dprev <= 1:
                return int(D), _i
        else:
            if Dprev - D <= 1:
                return int(D), _i
    raise


def get_y(
    i: int, j: int, x: int, token_amounts: List[int], D: int, amplification_factor: int
) -> Tuple[int, int]:
    """Calculate the y quantity in the stableswap invariant.
    """
    assert i != j
    assert j >= 0
    N_COINS = len(token_amounts)
    assert j < N_COINS

    assert i >= 0
    assert i < N_COINS

    Ann = amplification_factor * (N_COINS ** N_COINS)
    c = D
    S = 0
    _x = 0
    y_prev = 0

    for _i in range(N_COINS):
        if _i == i:
            _x = x
        elif _i != j:
            _x = token_amounts[_i]
        else:
            continue
        S += _x
        c = c * D // (_x * N_COINS)
    c = c * D * A_PRECISION // (Ann * N_COINS)
    b = S + D * A_PRECISION // Ann
    y = D
    for _i in range(255):
        y_prev = y
        y = (y * y + c) // (2 * y + b - D)
        if y > y_prev:
            if y - y_prev <= 1:
                return int(y), _i
        else:
            if y_prev - y <= 1:
                return int(y), _i
    raise