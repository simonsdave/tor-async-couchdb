"""The tamper module is intended to help add some tamper resistance
qualities to a CouchDB database. Each document written to the
CouchDB database is signed with an HMAC by the app tier using
a key that is accessible to only the app tier and the app tier
administrator. The key would not be accessible to the database
administrator. When a document is read from the CouchDB database
the signature is verified and if signature vertification fails
thet document is discarded after an alarm is raised.
"""

import json

_tampering_sig_prop_name = "801dbe4659a641739cbe94fcf0baab03_tampering_v1.0_sig"


def sign(signer, doc):
    """This method should be called just before ```doc``` (a dictionary)
    is written to CouchDB. The method adds a signature to ```doc``` using
    ```signer.Sign()```. It's assumed that ```signer``` is an instance
    of ```keyczar.Signer```. If ```signer.Sign()``` returns ```None```
    no signature is added to ```doc```.
    """
    (_, doc_as_utf8_str) = _prep_doc_for_signing_and_verification(doc)
    doc[_tampering_sig_prop_name] = signer.Sign(doc_as_utf8_str)
    return doc


def verify(signer, doc):
    """This method should be called just after ```doc``` (a dictionary)
    is read from CouchDB. The method verifies ```doc``` contains a valid
    a signature that was added by this module's ```sign()```. Signature
    verification is done by ```signer.Verify()```. It's assumed that
    ```signer``` is an instance of ```keyczar.Signer```.
    """
    (sig, doc_as_utf8_str) = _prep_doc_for_signing_and_verification(doc)
    if sig is None:
        return False
    # the try/except is here to catch the scenarios like the signature
    # being tampered with - try verifying a doc's signature using a
    # signature of "dave" and you'll understand the need
    try:
        return signer.Verify(doc_as_utf8_str, sig)
    except:
        pass
    return False


def _prep_doc_for_signing_and_verification(doc):
    """This method have an important and tricky responsiblity. This method
    takes a dictionary representing a document that's destined for or read
    from a CouchDB database and creates a UTF-8 encoded string representation
    of the dictionary that's suitable for have an HMAC calculated against.

    What's a little tricky about this method is:

        1/ CouchDB adds internal properties to a document when it's written
           to a database so these must be removed
        2/ converting a dictionary to a string via json.dumps() doesn't
           always produce consistent results so the keys in the dictionary
           need to be sorted

    Maybe tricky is the wrong way to describe this. Maybe (like so much
    crypto stuff) this is just a question of sweating the details.
    """
    doc_copy = doc.copy()
    doc_copy.pop("_id", None)
    doc_copy.pop("_rev", None)
    sig = doc_copy.pop(_tampering_sig_prop_name, None)
    doc_as_utf8_str = json.dumps(doc_copy, encoding="utf-8", sort_keys=True)
    return (sig, doc_as_utf8_str)
