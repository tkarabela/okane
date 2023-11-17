import okane
from lxml import etree


def test_zps():
    root = etree.XML("""\
    <Refs>
        <MsgId>1235</MsgId>
        <AcctSvcrRef>8765</AcctSvcrRef>
        <InstrId>PT120</InstrId>
        <EndToEndId>777124566</EndToEndId>
    </Refs>""")

    refs = okane.TransactionRef.from_xml(root)
    assert refs.message_id == "1235"
    assert refs.account_servicer_ref == "8765"
    assert refs.instruction_id == "PT120"
    assert refs.end_to_end_id == "777124566"


def test_sepa_ct():
    root = etree.XML("""\
    <Refs>
        <MsgId>1236</MsgId>
        <AcctSvcrRef>8764</AcctSvcrRef>
        <InstrId>MCCT110620000001</InstrId>
        <EndToEndId>E2EC110620000001</EndToEndId>
    </Refs>""")

    refs = okane.TransactionRef.from_xml(root)
    assert refs.message_id == "1236"
    assert refs.account_servicer_ref == "8764"
    assert refs.instruction_id == "MCCT110620000001"
    assert refs.end_to_end_id == "E2EC110620000001"


def test_sepa_dd():
    root = etree.XML("""\
    <Refs>
        <MsgId>1237</MsgId>
        <AcctSvcrRef>8763</AcctSvcrRef>
        <InstrId> MCCT110620000002</InstrId>
        <EndToEndId> E2EC110620000002</EndToEndId>
        <MndtId>8567464534</MndtId>
    </Refs>""")

    refs = okane.TransactionRef.from_xml(root)
    assert refs.message_id == "1237"
    assert refs.account_servicer_ref == "8763"
    assert refs.instruction_id == "MCCT110620000002"
    assert refs.end_to_end_id == "E2EC110620000002"
    assert refs.mandate_id == "8567464534"


def test_card_transaction():
    root = etree.XML("""\
    <Refs>
        <MsgId>1238</MsgId>
        <AcctSvcrRef>8762</AcctSvcrRef>
        <PmtInfId>1567805</PmtInfId>
        <EndToEndId>777124567</EndToEndId>
        <ChqNb>xxxxxxxxxxxx1234</ChqNb>
        <ClrSysRef>systemovy text</ClrSysRef>
    </Refs>""")

    refs = okane.TransactionRef.from_xml(root)
    assert refs.message_id == "1238"
    assert refs.account_servicer_ref == "8762"
    assert refs.payment_invocation_id == "1567805"
    assert refs.cheque_number == "xxxxxxxxxxxx1234"
    assert refs.end_to_end_id == "777124567"
    assert refs.clearing_system_ref == "systemovy text"
