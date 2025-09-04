import sys

from oaipmh import common

if sys.version_info[0] == 3:
    text_type = str
else:
    text_type = unicode

class MetadataRegistry(object):
    """A registry that contains readers and writers of metadata.

    a reader is a function that takes a chunk of (parsed) XML and
    returns a metadata object.

    a writer is a function that takes a takes a metadata object and
    produces a chunk of XML in the right format for this metadata.
    """
    def __init__(self):
        self._readers = {}
        self._writers = {}

    def registerReader(self, metadata_prefix, reader):
        self._readers[metadata_prefix] = reader

    def registerWriter(self, metadata_prefix, writer):
        self._writers[metadata_prefix] = writer

    def hasReader(self, metadata_prefix):
        return metadata_prefix in self._readers

    def hasWriter(self, metadata_prefix):
        return metadata_prefix in self._writers

    def readMetadata(self, metadata_prefix, element):
        """Turn XML into metadata object.

        element - element to read in

        returns - metadata object
        """
        return self._readers[metadata_prefix](element)

    def writeMetadata(self, metadata_prefix, element, metadata):
        """Write metadata as XML.

        element - ElementTree element to write under
        metadata - metadata object to write
        """
        self._writers[metadata_prefix](element, metadata)

global_metadata_registry = MetadataRegistry()

class Error(Exception):
    pass

class MetadataReader(object):
    """A default implementation of a reader based on fields.
    """
    def __init__(self, fields, namespaces=None):
        self._fields = fields
        self._namespaces = namespaces or {}

    def __call__(self, element):
        map = {}
        e = element.xpath
        # now extra field info according to xpath expr
        for field_name, (field_type, expr) in list(self._fields.items()):
            if field_type == 'bytes':
                value = str(e(expr, namespace=self._namespaces))
            elif field_type == 'bytesList':
                value = [str(item) for item in e(expr, namespace=self._namespaces)]
            elif field_type == 'text':
                # make sure we get back unicode strings instead
                # of lxml.etree._ElementUnicodeResult objects.
                value = text_type(e(expr, namespace=self._namespaces))
            elif field_type == 'textList':
                # Make sure we get back unicode strings instead
                # of lxml.etree._ElementUnicodeResult objects.

                # Run the XPath query and get the result
                result = e(expr, namespace=self._namespaces)

                # Check if the result is a list. If not, treat it as a single item.
                if isinstance(result, list):
                    # The result is a list, so iterate and convert each element
                    value = [text_type(v) for v in result]
                elif result is not None:
                    # The result is a single value, so wrap it in a list
                    value = [text_type(result)]
                else:
                    # The result is None (e.g., no match), so return an empty list
                    value = []
            else:
                raise Error("Unknown field type: %s" % field_type)
            map[field_name] = value
        return common.Metadata(element, map)

oai_dc_reader = MetadataReader(
    fields={
    'title':       ('textList', 'oai_dc:dc/dc:title/text()'),
    'creator':     ('textList', 'oai_dc:dc/dc:creator/text()'),
    'subject':     ('textList', 'oai_dc:dc/dc:subject/text()'),
    'description': ('textList', 'oai_dc:dc/dc:description/text()'),
    'publisher':   ('textList', 'oai_dc:dc/dc:publisher/text()'),
    'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
    'date':        ('textList', 'oai_dc:dc/dc:date/text()'),
    'type':        ('textList', 'oai_dc:dc/dc:type/text()'),
    'format':      ('textList', 'oai_dc:dc/dc:format/text()'),
    'identifier':  ('textList', 'oai_dc:dc/dc:identifier/text()'),
    'source':      ('textList', 'oai_dc:dc/dc:source/text()'),
    'language':    ('textList', 'oai_dc:dc/dc:language/text()'),
    'relation':    ('textList', 'oai_dc:dc/dc:relation/text()'),
    'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
    'rights':      ('textList', 'oai_dc:dc/dc:rights/text()')
    },
    namespaces={
    'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc' : 'http://purl.org/dc/elements/1.1/'}
    )
