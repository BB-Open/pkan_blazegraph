# -*- coding: utf-8 -*-
"""Tripel store access"""

import requests
from SPARQLWrapper import SPARQLWrapper2

from pkan.blazegraph.constants import BLAZEGRAPH_BASE
from pkan.blazegraph.errors import HarvestURINotReachable, TripelStoreBulkLoadError, TripelStoreCreateNamespaceError


class SPARQL(object):
    """
    API to the SPARQL Endpoint of a namespace
    """

    def __init__(self, uri):
        self.sparql = SPARQLWrapper2(uri)

    def exists(self, URI):
        self.sparql.setQuery("""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?s
            WHERE { ?s ?p ?o }
                    """)
        results = self.sparql.query()
        if results:
            return True

    def insert(self, tripel):
        queryString = """INSERT DATA
           {{ GRAPH <http://example.com/> {{ {s} {p} {o} }} }}"""

        self.sparql.setQuery(
            queryString.format(s=tripel.s, o=tripel.o, p=tripel.p))
        self.sparql.method = 'POST'
        self.sparql.query()

    def query(self, queryString):
        self.sparql.setQuery(queryString)
        results = self.sparql.query()
        return results


class Tripelstore(object):
    """
    API to the tripelstore
    """

    def __init__(self, blazegraph_base=None):

        self.namespace_uris = {}
        if blazegraph_base:
            self.blazegraph_base = blazegraph_base
        else:
            self.blazegraph_base = BLAZEGRAPH_BASE

    def sparql_for_namespace(self, namespace):
        if namespace not in self.namespace_uris:
            self.generate_namespace_uri(namespace)
        return SPARQL(self.namespace_uris[namespace])

    def rest_create_namespace(self, namespace):
        """
        Creates a namespace in the tripelstore and registers
        a namespace sparqlwrapper for it
        :param namespace: Then namespace to be created
        :return:
        """
        params = """
        com.bigdata.rdf.sail.namespace={namespace}
        com.bigdata.rdf.sail.truthMaintenance=false
        com.bigdata.namespace.{namespace}.spo.com.bigdata.btree.BTree.branchingFactor=1024
        com.bigdata.rdf.store.AbstractTripleStore.textIndex=true
        com.bigdata.rdf.store.AbstractTripleStore.justify=false
        com.bigdata.rdf.store.AbstractTripleStore.statementIdentifiers=false
        com.bigdata.rdf.store.AbstractTripleStore.axiomsClass=com.bigdata.rdf.axioms.NoAxioms
        com.bigdata.rdf.store.AbstractTripleStore.quads=false
        com.bigdata.namespace.{namespace}.lex.com.bigdata.btree.BTree.branchingFactor=400
        com.bigdata.rdf.store.AbstractTripleStore.geoSpatial=false
        com.bigdata.journal.Journal.groupCommit=false
        com.bigdata.rdf.sail.isolatableIndices=false
        """.format(namespace=namespace)
        headers = {'content-type': 'text/plain'}
        response = requests.post(
            self.blazegraph_base + '/blazegraph/namespace',
            data=params,
            headers=headers,
        )
        self.generate_namespace_uri(namespace)

        return response

    def generate_namespace_uri(self, namespace):
        blaze_uri = self.blazegraph_base + \
                    '/blazegraph/namespace/{namespace}/sparql'
        blaze_uri_with_namespace = blaze_uri.format(namespace=namespace)
        self.namespace_uris[namespace] = blaze_uri_with_namespace
        return blaze_uri_with_namespace

    def rest_bulk_load_from_uri(self, namespace, uri, content_type):
        """
        Load the tripel_data from the harvest uri
        and push it into the tripelstore
        :param namespace:
        :param uri:
        :param content_type:
        :return:
        """
        # Load the tripel_data from the harvest uri
        response = requests.get(uri)
        if response.status_code != 200:
            raise HarvestURINotReachable(response.content)
        tripel_data = response.content

        # push it into the tripelstore
        blaze_uri_with_namespace = self.generate_namespace_uri(namespace)
        headers = {'Content-Type': content_type}
        response = requests.post(
            blaze_uri_with_namespace,
            data=tripel_data,
            headers=headers,
        )
        return response

    def graph_from_uri(self, namespace, uri, content_type):
        self.create_namespace(namespace)
        response = self.rest_bulk_load_from_uri(namespace, uri, content_type)
        if response.status_code == 200:
            return self.sparql_for_namespace(namespace), response
        else:
            raise TripelStoreBulkLoadError(response.content)

    def create_namespace(self, namespace):
        response = self.rest_create_namespace(namespace)
        if response.status_code in [200, 201, 409]:
            return self.sparql_for_namespace(namespace)
        else:
            msg = str(response.status_code) + ': ' + response.content
            raise TripelStoreCreateNamespaceError(msg)

    def move_data_between_namespaces(self, target_namespace, source_namespace):
        self.create_namespace(source_namespace)
        self.create_namespace(target_namespace)
        source = self.generate_namespace_uri(source_namespace)
        target = self.generate_namespace_uri(target_namespace)
        mime_type = 'application/rdf+xml'
        headers = {
            'Accept': mime_type,
        }

        data = {
            'query': 'CONSTRUCT  WHERE { ?s ?p ?o }'
        }

        response = requests.post(source, headers=headers, data=data)
        tripel_data = response.content

        headers = {'Content-Type': mime_type}
        response = requests.post(
            target,
            data=tripel_data,
            headers=headers,
        )

        return response

    def get_turtle_from_query(self, namespace, query):

        mime_type = 'text/turtle'
        tripel_data = self.get_triple_data_from_query(namespace, query, mime_type)
        return tripel_data

    def get_triple_data_from_query(self, namespace, query, mime_type):
        self.create_namespace(namespace)
        source = self.generate_namespace_uri(namespace)

        headers = {
            'Accept': mime_type
        }

        data = {'query': query}
        response = requests.post(source, headers=headers, data=data)
        tripel_data = response.content

        return tripel_data


# ToDo make to utility
tripel_store = Tripelstore()
