import bson
import os
import ssl
import unittest
from threading import Thread
from wsgit.server import Server
from tests.applications import various_status_application as app
from socket import socket, SOCK_STREAM, AF_INET


class TestServer(unittest.TestCase):

    def test_server(self):
        bson.patch_socket()
        server, thread = Server.run_server(('127.0.0.1', 9338), app)
        conn = socket(AF_INET, SOCK_STREAM)
        conn.connect(('127.0.0.1', 9338))
        conn.sendobj({'url': '/'})
        self.assertEqual(conn.recvobj(), dict(
            status=dict(reason='OK', code='200')))
        server.shutdown()

    def test_ssl(self):
        def make_keys():
            from OpenSSL import crypto
            from socket import gethostname
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 1024)

            cert = crypto.X509()
            cert.get_subject().C = "KR"
            cert.get_subject().L = "LocalityName"
            cert.get_subject().O = "OrganizationName"
            cert.get_subject().OU = "OrganizationUnitName"
            cert.get_subject().CN = gethostname()
            cert.set_serial_number(12345)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(k)
            cert.sign(k, 'sha1')
            open('ssl.crt', 'wt').write(
                crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            open('ssl.key', 'wt').write(
                crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

        def destroy_keys():
            os.remove('ssl.crt')
            os.remove('ssl.key')

        make_keys()
        bson.patch_socket()
        server, thread = Server.run_server(('127.0.0.1', 9339), app, ssl=True)
        conn = socket(AF_INET, SOCK_STREAM)
        conn = ssl.wrap_socket(conn,
                               keyfile='ssl.key',
                               certfile='ssl.crt',
                               ssl_version=ssl.PROTOCOL_TLSv1)
        conn.connect(('127.0.0.1', 9339))
        conn.sendobj({'url': '/'})
        self.assertEqual(conn.recvobj(), dict(
            status=dict(reason='OK', code='200')))
        server.shutdown()
        destroy_keys()