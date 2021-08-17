from enum import Enum, auto
from unicodedata import is_normalized

from .. import ExtractionError

class Tag(Enum):
    TITLE = auto()
    DURATION = auto()
    ALBUM = auto()
    ARTIST = auto()
    ALBUM_ARTIST = auto()
    DISC_NO = auto()
    DISC_TOTAL = auto()
    YEAR = auto()
    TRACK_NO = auto()
    TRACK_TOTAL = auto()
    GENRE = auto()
    COMPOSER = auto()
    COVER_ART = auto()  # we only allow at most one cover art.


CORE_TAGS = {
    Tag.TITLE,
    Tag.ALBUM,
    Tag.ARTIST,
    Tag.ALBUM_ARTIST,
    Tag.DISC_NO,
    Tag.DISC_TOTAL,
    Tag.YEAR,
    Tag.TRACK_NO,
    Tag.TRACK_TOTAL,
    Tag.GENRE,
    Tag.DURATION,
}

TagTypeMap = {
    Tag.TITLE: str,
    Tag.ALBUM: str,
    Tag.ARTIST: str,
    Tag.ALBUM_ARTIST: str,
    Tag.DISC_NO: int,
    Tag.DISC_TOTAL: int,
    Tag.YEAR: int,
    Tag.DURATION: float,  # in seconds.
    Tag.TRACK_NO: int,
    Tag.TRACK_TOTAL: int,
    Tag.GENRE: str,
    Tag.COMPOSER: str,
    Tag.COVER_ART: str,
}


def check_valid_metadata(extracted, ext):
    if ext == '.iso':
        assert type(extracted) is list
        assert len(extracted) > 0
        for extracted_inner in extracted:
            check_valid_metadata_one(extracted_inner)
    else:
        check_valid_metadata_one(extracted)


def check_valid_metadata_one(extracted):
    try:
        assert extracted.keys() == set(Tag)
        for tag in Tag:
            value = extracted[tag]
            if tag in CORE_TAGS and value is None:
                raise ValueError("core tag {} cannot be None".format(tag))

            if value is not None:
                if type(value) is not TagTypeMap[tag]:
                    raise ValueError('{} is not of type {}'.format(repr(value), TagTypeMap[tag]))

                if type(value) is str:
                    assert value != ''
                    assert value == value.strip()
                    # let's handle this issue later on. all normalization forms are fine.
                    # we can normalize them internally later.
                    if not (is_normalized('NFC', value) or is_normalized('NFD', value)):
                        raise ExtractionError(f'unnormalized Unicode data {repr(value)}')
                # TODO: more detailed checking can be done later.

    except Exception as e:
        raise RuntimeError(
            "invalid metadata {}".format(extracted), e
        )
