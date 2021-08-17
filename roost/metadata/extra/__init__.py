import plistlib
from enum import Enum, auto
from urllib.parse import urlparse, unquote
from unicodedata import is_normalized, normalize
from .. import ExtractionError


class Extra(Enum):
    RATING = auto()  # integer 0 - 100
    LOVE = auto()  # can only take true, or null
    HATE = auto()  # can only take true, or null
    # TODO: disable this for now, as Music app does not export lyrics and I don't bother
    #   to extract the lyrics from metadata.
    # LYRICS = auto()  # free form string
    COMMENT = auto()  # free form string


TagTypeMap = {
    Extra.RATING: int,
    Extra.LOVE: bool,
    Extra.HATE: bool,
    Extra.COMMENT: str,
}


def convert_itunes_xml(xml_path, comments_to_skip=None):
    with open(xml_path, 'rb') as f_plist:
        z = plistlib.load(f_plist)
    ret = dict()
    for track in z['Tracks'].values():
        assert 'Location' in track
        path_to_add = unquote(urlparse(track['Location']).path)
        path_to_add = normalize('NFD', path_to_add)
        assert path_to_add not in ret

        meta_this = {
            Extra.RATING: track.get('Rating', None),
            Extra.LOVE: track.get('Loved', None),
            Extra.HATE: track.get('Disliked', None),
            Extra.COMMENT: track.get('Comments', None),
        }

        if comments_to_skip is not None and meta_this[Extra.COMMENT] in comments_to_skip:
            meta_this[Extra.COMMENT] = None

        ret[path_to_add] = meta_this

    return ret


def create_empty_extra_metadata():
    return {
        k: None for k in Extra
    }


def check_valid_extra_metadata(extracted, ext):
    if ext == '.iso':
        assert type(extracted) is list
        assert len(extracted) > 0
        for extracted_inner in extracted:
            check_valid_extra_metadata_one(extracted_inner)
    else:
        check_valid_extra_metadata_one(extracted)


def check_valid_extra_metadata_one(extracted):
    try:
        assert extracted.keys() == set(Extra)
        for tag in Extra:
            value = extracted[tag]
            if value is not None:
                if type(value) is not TagTypeMap[tag]:
                    raise ValueError('{} is not of type {}'.format(repr(value), TagTypeMap[tag]))

                if type(value) is int:
                    assert value in {20, 40, 60, 80, 100}

                if type(value) is str:
                    assert value != ''
                    # let's handle this issue later on. all normalization forms are fine.
                    # we can normalize them internally later.
                    if not (is_normalized('NFC', value) or is_normalized('NFD', value)):
                        raise ExtractionError(f'unnormalized Unicode data {repr(value)}')

                if type(value) is bool:
                    assert value, "boolean values here should not take False"

    except Exception as e:
        raise RuntimeError(
            "invalid metadata {}".format(extracted), e
        )
