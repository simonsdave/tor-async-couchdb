"""This module contains a collection of utility logic that implements
a CouchDB database installer. To use this module create design documents
as JSON files (just like CouchDB would expect) and then
create a mainline for the installer like the example in
samples/db_installer/installer.py

And that's all there is too it! Pretty sweet right?:-)
"""

import glob
import httplib
import json
import logging
import optparse
import os
import requests

from keyczar import keyczar

import clparserutil
import tamper

_logger = logging.getLogger(__name__)


def _is_couchdb_accessible(host, session, verify_host_ssl_cert):
    """Returns True if there's a CouchDB server running on ```host```.
    Otherwise returns False.
    """
    try:
        response = session.get(host, verify=verify_host_ssl_cert)
    except Exception:
        return False

    return response.status_code == httplib.OK


def _create_database(database, host, session, verify_host_ssl_cert):
    _logger.info("Creating database '%s' on '%s'", database, host)

    url = "%s/%s" % (host, database)
    response = session.head(url, verify=verify_host_ssl_cert)
    if response.status_code == httplib.OK:
        _logger.info("Database '%s' on '%s' already exist", database, host)
        return True
    response = session.put(url, verify=verify_host_ssl_cert)
    if response.status_code != httplib.CREATED:
        _logger.error("Failed to create database '%s' on '%s'", database, host)
        return False
    _logger.info("Successfully created database '%s' on '%s'", database, host)

    return True


def _create_design_docs(database,
                        host,
                        session,
                        verify_host_ssl_cert,
                        design_docs_folder):
    #
    # iterate thru each file in the design doc module's directory
    # for files that end with ".py" - these files are assumed to be
    # JSON design documents with the filename (less ".py" being the
    # design document name
    #
    _logger.info(
        "Creating design documents in database '%s' on '%s'",
        database,
        host)

    design_doc_filename_pattern = os.path.join(design_docs_folder, "*.json")
    for design_doc_filename in glob.glob(design_doc_filename_pattern):

        design_doc_name = os.path.basename(design_doc_filename)[:-len(".json")]
        url = "%s/%s/_design/%s" % (host, database, design_doc_name)

        response = session.head(url, verify=verify_host_ssl_cert)
        if response.status_code == httplib.OK:
            _logger.info(
                "Design doc '%s' already exist in database '%s' on '%s'",
                design_doc_name, database, host)
            continue

        _logger.info(
            "Creating design doc '%s' in database '%s' on '%s' from file '%s'",
            design_doc_name,
            database,
            host,
            design_doc_filename)

        with open(design_doc_filename, "r") as design_doc_file:
            design_doc = design_doc_file.read()

        response = session.put(
            url,
            data=design_doc,
            headers={"Content-Type": "application/json; charset=utf8"},
            verify=verify_host_ssl_cert)
        if response.status_code != httplib.CREATED:
            _logger.error("Failed to create design doc '%s'", url)
            return False
        _logger.info("Successfully created design doc '%s'", url)

    return True


def _create_seed_docs(database,
                      host,
                      session,
                      verify_host_ssl_cert,
                      seed_docs_folder,
                      seed_doc_signer_dir_name):
    #
    # iterate thru each file in the seed doc module's directory
    # for files that end with ".py" - these files are assumed to be
    # JSON documents. The filename is ignored.
    #
    _logger.info(
        "Creating seed documents in database '%s' on '%s'",
        database,
        host)

    seed_doc_signer = None
    if seed_doc_signer_dir_name:
        try:
            seed_doc_signer = keyczar.Signer.Read(seed_doc_signer_dir_name)
        except:
            _logger.error(
                "Error creating seed doc signer from '%s'",
                seed_doc_signer_dir_name)
            return False

    seed_doc_filename_pattern = os.path.join(seed_docs_folder, "*.json")
    for seed_doc_filename in glob.glob(seed_doc_filename_pattern):

        _logger.info(
            "Creating seed doc in database '%s' on '%s' from file '%s'",
            database,
            host,
            seed_doc_filename)

        with open(seed_doc_filename, "r") as seed_doc_file:
            seed_doc = seed_doc_file.read()

        try:
            json.loads(seed_doc)
        except Exception as ex:
            _logger.error(
                "Failed to create seed doc from '%s' - invalid JSON '%s'",
                seed_doc_filename,
                ex)
            return False

        if seed_doc_signer is not None:
            seed_doc = json.loads(seed_doc)
            tamper.sign(seed_doc_signer, seed_doc)
            seed_doc = json.dumps(seed_doc)

        url = "%s/%s" % (host, database)
        response = session.post(
            url,
            data=seed_doc,
            headers={"Content-Type": "application/json; charset=utf8"},
            verify=verify_host_ssl_cert)
        if response.status_code != httplib.CREATED:
            _logger.error("Failed to create seed doc from '%s'", seed_doc_filename)
            return False
        _logger.info(
            "Successfully created seed doc '%s' from '%s'",
            response.headers["location"],
            seed_doc_filename)

    return True


def _delete_database(database, host, session, verify_host_ssl_cert):
    _logger.info("Deleting database '%s' on '%s'", database, host)

    url = "%s/%s" % (host, database)
    response = session.get(url, verify=verify_host_ssl_cert)
    if response.status_code == httplib.NOT_FOUND:
        fmt = (
            "No need to delete database '%s' on '%s' "
            "since database doesn't exist"
        )
        _logger.info(fmt, database, host)
        return True

    url = "%s/%s" % (host, database)
    response = session.delete(url, verify=verify_host_ssl_cert)
    if response.status_code != httplib.OK:
        _logger.error("Failed to delete database '%s' on '%s'", database, host)
        return False

    _logger.info("Successfully deleted database '%s' on '%s'", database, host)
    return True


class CommandLineParser(optparse.OptionParser):
    """```CommandLineParser``` is an abstract base class used to
    parse command line arguments for a CouchDB installer.
    See this module's complete example for how to use this class."""

    def __init__(self, description, default_database):

        optparse.OptionParser.__init__(
            self,
            "usage: %prog [options]",
            description=description,
            option_class=clparserutil.Option)

        default = logging.ERROR
        fmt = (
            "logging level [DEBUG,INFO,WARNING,ERROR,CRITICAL,FATAL] - "
            "default = %s"
        )
        help = fmt % logging.getLevelName(default)
        self.add_option(
            "--log",
            action="store",
            dest="logging_level",
            default=default,
            type="logginglevel",
            help=help)

        default = "http://127.0.0.1:5984"
        help = "where's CouchDB running - default = %s" % default
        self.add_option(
            "--host",
            action="store",
            dest="host",
            default=default,
            type="schemehostport",
            help=help)

        default = default_database
        help = "database - default = %s" % default
        self.add_option(
            "--database",
            action="store",
            dest="database",
            default=default,
            type="string",
            help=help)

        help = "creds - optional; format = user:password"
        self.add_option(
            "--creds",
            action="store",
            dest="creds",
            default=None,
            type="usercolonpassword",
            help=help)

        default = False
        help = "delete before creating database - default = %s" % default
        self.add_option(
            "--delete",
            action="store",
            dest="delete",
            default=default,
            type="boolean",
            help=help)

        default = True
        help = "create database - default = %s" % default
        self.add_option(
            "--create",
            action="store",
            dest="create",
            default=default,
            type="boolean",
            help=help)

        default = True
        help = "create design docs - default = %s" % default
        self.add_option(
            "--createdesign",
            action="store",
            dest="create_design_docs",
            default=default,
            type="boolean",
            help=help)

        default = True
        help = "create seed docs - default = %s" % default
        self.add_option(
            "--createseed",
            action="store",
            dest="create_seed_docs",
            default=default,
            type="boolean",
            help=help)

        default = ""
        help = "sign seed docs with this signer - default = %s" % default
        self.add_option(
            "--seeddocsigner",
            action="store",
            dest="seed_doc_signer_dir_name",
            default=default,
            type="string",
            help=help)

        default = True
        help = "verify host's SSL certificate - default = %s" % default
        self.add_option(
            "--verify_host_ssl_cert",
            action="store",
            dest="verify_host_ssl_cert",
            default=default,
            type="boolean",
            help=help)


def main(clp, design_docs_module=None, seeds_docs_module=None):
    """```main``` is used to implement the core main line logic
    for a CouchDB installer. See this module's complete example
    for how to use this class."""

    (clo, cla) = clp.parse_args()

    logging.basicConfig(level=clo.logging_level)

    session = requests.Session()

    if clo.creds:
        session.auth = (clo.creds.user, clo.creds.password)

    is_ok = _is_couchdb_accessible(
        clo.host,
        session,
        clo.verify_host_ssl_cert)
    if not is_ok:
        _logger.fatal("CouchDB isn't running on '%s'", clo.host)
        return 1

    if clo.delete:
        is_ok = _delete_database(
            clo.database,
            clo.host,
            session,
            clo.verify_host_ssl_cert)
        if not is_ok:
            return 1

    if clo.create:
        is_ok = _create_database(
            clo.database,
            clo.host,
            session,
            clo.verify_host_ssl_cert)
        if not is_ok:
            return 1

    if clo.create and clo.create_design_docs and design_docs_module is not None:
        is_ok = _create_design_docs(
            clo.database,
            clo.host,
            session,
            clo.verify_host_ssl_cert,
            design_docs_module)
        if not is_ok:
            return 1

    if clo.create and clo.create_seed_docs and seeds_docs_module is not None:
        is_ok = _create_seed_docs(
            clo.database,
            clo.host,
            session,
            clo.verify_host_ssl_cert,
            seeds_docs_module,
            clo.seed_doc_signer_dir_name)
        if not is_ok:
            return 1

    return 0
