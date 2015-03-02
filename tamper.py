"""...
"""

import json

_tampering_sig_prop_name = "801dbe4659a641739cbe94fcf0baab03_tampering_v1.0_sig"

def sign(signer, doc):
    (_, doc_as_utf8_str) = _prep_doc_for_signing_and_verification(doc)
    sig = signer.Sign(doc_as_utf8_str)
    if sig is not None:
        doc[_tampering_sig_prop_name] = sig
    return doc

def verify(signer, doc):
    (sig, doc_as_utf8_str) = _prep_doc_for_signing_and_verification(doc)
    return signer.Verify(doc_as_utf8_str, sig)

def _prep_doc_for_signing_and_verification(doc):
    doc_copy = doc.copy()
    doc_copy.pop("_id", None)
    doc_copy.pop("_rev", None)
    sig = doc_copy.pop(_tampering_sig_prop_name, None)
    doc_as_utf8_str = json.dumps(doc_copy, encoding="utf-8", sort_keys=True)
    return (sig, doc_as_utf8_str)
