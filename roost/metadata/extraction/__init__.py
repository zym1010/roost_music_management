from subprocess import check_output
from xml.etree import ElementTree


def extract_meta(file_name_full):
    return ElementTree.fromstring(
        check_output(
            # special characeters (<, >, etc.) are escaped,
            # and xml package will handle them correctly.
            ["exiftool", "-X", file_name_full]
        )
    )
