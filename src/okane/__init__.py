# ruff: noqa: F401
"""
Okane
=====

Python parser for bank statements in camt.053 XML format, in dialect
used by the Czech Banking Association (ČBA).

"""

from .models import BankId, Balance, AccountId, BankToCustomerStatement, Transaction, TransactionRef
from .cli import main

__version__ = "0.2.0"
