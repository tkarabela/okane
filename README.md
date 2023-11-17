[![CI - build](https://img.shields.io/github/actions/workflow/status/tkarabela/okane/main.yml?branch=master)](https://github.com/tkarabela/okane/actions)
[![CI - coverage](https://img.shields.io/codecov/c/github/tkarabela/okane)](https://app.codecov.io/github/tkarabela/okane)
![MyPy checked](http://www.mypy-lang.org/static/mypy_badge.svg)
![PyPI - Version](https://img.shields.io/pypi/v/okane.svg?style=flat-square)
![PyPI - Status](https://img.shields.io/pypi/status/okane.svg?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/okane.svg?style=flat-square)
![License](https://img.shields.io/pypi/l/okane.svg?style=flat-square)

# お<ruby>金<rt>かね</rt></ruby> 【okane】

_okane_ is a pure Python parser for bank statements in camt.053 XML format [[1]], in dialect
used by the Czech Banking Association (ČBA) [[2]].

It parses `BkToCstmrStmt` XML element into `okane.BankToCustomerStatement` which is
a Pydantic model. It can also work as a CLI tool, converting camt.053 XML files to JSON or CSV.

## Installation

```shell
pip install okane

# or, if you'd like to use the CSV, XLSX export features and access the data as `pd.DataFrame`
pip install okane[pandas]
```

## Example

### Python API

    >>> import okane
    >>> statement = okane.BankToCustomerStatement.from_file("./tests/data/test2.xml")
    >>> statement.opening_balance
    Balance(amount=Decimal('1000.00'), currency='CZK', date=datetime.date(2023, 3, 1))
    >>> statement.transactions[5].amount
    Decimal('1000.00')
    >>> statement.transactions[5].currency
    'CZK'
    >>> statement.transactions[5].related_account_id
    AccountId(iban='LT6632xxxxxx', id=None)
    >>> statement.transactions[5].related_account_bank_id
    BankId(bic='REVOLT21', id=None)
    >>> statement.transactions[3].ref
    TransactionRef(message_id='XXX', end_to_end_id='XXX', account_servicer_ref=None, payment_invocation_id=None, instruction_id=None, mandate_id=None, cheque_number=None, clearing_system_ref=None)
    >>> df = statement.as_dataframe()

### Command-line interface

```shell
head ./tests/data/test2.xml
```

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
    <BkToCstmrStmt>
        <GrpHdr>
            <MsgId>camt.053-2023-04-01-001</MsgId>
            <CreDtTm>2023-04-01T12:00:00.000+02:00</CreDtTm>
            <MsgRcpt>
                <Nm>John Doe</Nm>
```

```shell
# okane ./tests/data/test*.xml -f json --no-indent -o output.jsonl
# okane ./tests/data/test*.xml -f csv -o output.csv
# okane ./tests/data/test*.xml -f xlsx -o output.xlsx

okane ./tests/data/test2.xml
```

```json
{
    "statement_id": "XXX-STATEMENT-ID",
    "created_time": "2023-04-01T12:00:00+02:00",
    "from_time": "2023-03-01T00:00:00+01:00",
    "to_time": "2023-03-31T23:59:59.999000+02:00",
    "account_id": {
        "iban": "XXX-IBAN",
        "id": null
    },
    "opening_balance": {
        "amount": "1000.00",
        "currency": "CZK",
        "date": "2023-03-01"
    },
    "closing_balance": {
        "amount": "2000.00",
        "currency": "CZK",
        "date": "2023-03-31"
    },
    "transactions": [
        {
            "ref": {
                "message_id": "XXX",
                "end_to_end_id": "XXX",
                "account_servicer_ref": null,
                "payment_invocation_id": null,
                "instruction_id": null,
                "mandate_id": null,
                "cheque_number": null,
                "clearing_system_ref": null
            },
            "entry_ref": "XXX-REF-1",
            "amount": "-100.00",
            "currency": "CZK",
            "val_date": "2023-03-01",
            "remote_info": "Nákup dne 27.2.2023, částka 100.00 CZK",
            "additional_transaction_info": "Nákup dne 27.2.2023, částka 100.00 CZK",
            "related_account_id": null,
            "related_account_bank_id": null
        },
        {
            "ref": {
                "message_id": "XXX",
                "end_to_end_id": "XXX",
                "account_servicer_ref": null,
                "payment_invocation_id": null,
                "instruction_id": null,
                "mandate_id": null,
                "cheque_number": null,
                "clearing_system_ref": null
            },
            "entry_ref": "XXX-REF-2",
            "amount": "-200.00",
            "currency": "CZK",
            "val_date": "2023-03-02",
            "remote_info": null,
            "additional_transaction_info": "transaction note",
            "related_account_id": {
                "iban": null,
                "id": "XXX-OTHER-ACC"
            },
            "related_account_bank_id": {
                "bic": null,
                "id": "XXX-OTHER-BANK"
            }
        },
        {
            "ref": {
                "message_id": "XXX",
                "end_to_end_id": null,
                "account_servicer_ref": null,
                "payment_invocation_id": null,
                "instruction_id": null,
                "mandate_id": null,
                "cheque_number": null,
                "clearing_system_ref": null
            },
            "entry_ref": "XXX-REF-3",
            "amount": "1000.00",
            "currency": "CZK",
            "val_date": "2023-03-07",
            "remote_info": null,
            "additional_transaction_info": null,
            "related_account_id": {
                "iban": null,
                "id": "XXX-OTHER-ACC"
            },
            "related_account_bank_id": {
                "bic": null,
                "id": "XXX-OTHER-BANK"
            }
        },
        {
            "ref": {
                "message_id": "XXX",
                "end_to_end_id": "XXX",
                "account_servicer_ref": null,
                "payment_invocation_id": null,
                "instruction_id": null,
                "mandate_id": null,
                "cheque_number": null,
                "clearing_system_ref": null
            },
            "entry_ref": "XXX-REF-4",
            "amount": "400.00",
            "currency": "CZK",
            "val_date": "2023-03-08",
            "remote_info": "description",
            "additional_transaction_info": "RECIPIENT NAME",
            "related_account_id": {
                "iban": null,
                "id": "XXX-OTHER-ACC"
            },
            "related_account_bank_id": {
                "bic": null,
                "id": "XXX-OTHER-BANK"
            }
        },
        {
            "ref": {
                "message_id": "XXX",
                "end_to_end_id": "XXX",
                "account_servicer_ref": null,
                "payment_invocation_id": null,
                "instruction_id": null,
                "mandate_id": null,
                "cheque_number": null,
                "clearing_system_ref": null
            },
            "entry_ref": "XXX-REF-5",
            "amount": "-100.00",
            "currency": "CZK",
            "val_date": "2023-03-31",
            "remote_info": "transaction description",
            "additional_transaction_info": null,
            "related_account_id": null,
            "related_account_bank_id": null
        },
        {
            "ref": {
                "message_id": "XXX",
                "end_to_end_id": null,
                "account_servicer_ref": null,
                "payment_invocation_id": null,
                "instruction_id": null,
                "mandate_id": null,
                "cheque_number": null,
                "clearing_system_ref": null
            },
            "entry_ref": "XXX-REF-6",
            "amount": "1000.00",
            "currency": "CZK",
            "val_date": "2023-03-07",
            "remote_info": null,
            "additional_transaction_info": null,
            "related_account_id": {
                "iban": "LT6632xxxxxx",
                "id": null
            },
            "related_account_bank_id": {
                "bic": "REVOLT21",
                "id": null
            }
        }
    ]
}
```


## License

MIT – see [LICENSE.txt](./LICENSE.txt).

[1]: https://www.iso20022.org/iso-20022-message-definitions?search=camt.053
[2]: https://cbaonline.cz/formaty-xml-pro-vzajemnou-komunikaci-bank-s-klienty

## Changelog

### 0.2.0

- Added `AccountId`, `BankId` models to handle IBAN/BIC codes
- Added `TransactionRef` model to store transaction references, eg. end-to-end reference
- Pandas integration: `BankToCustomerStatement.as_dataframe()`
- Pandas integration: `okane` CLI tool can merge multiple input XMLs into one CSV/XLSX
- Upgraded Pydantic version from 1.10 to 2.5

### 0.1.0

- Initial release
