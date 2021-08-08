from subprocess import check_output
from xml.etree import ElementTree


class ExtractionError(Exception):
    pass


def extract_meta(file_name_full):
    return ElementTree.fromstring(
        check_output(
            # special characeters (<, >, etc.) are escaped,
            # and xml package will handle them correctly.
            # '-n' will make time shown in raw seconds, rather than prettified HH:MM:SS.
            ["exiftool", "-n", "-X", file_name_full]
        )
    )
