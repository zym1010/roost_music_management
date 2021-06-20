from enum import Enum, auto


class Tag(Enum):
    TITLE = auto()
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
}

TagTypeMap = {
    Tag.TITLE: str,
    Tag.ALBUM: str,
    Tag.ARTIST: str,
    Tag.ALBUM_ARTIST: str,
    Tag.DISC_NO: int,
    Tag.DISC_TOTAL: int,
    Tag.YEAR: int,
    Tag.TRACK_NO: int,
    Tag.TRACK_TOTAL: int,
    Tag.GENRE: str,
    Tag.COMPOSER: str,
}


def check_valid_metadata(extracted):
    try:
        for tag in Tag:
            value = extracted[tag]
            if tag in CORE_TAGS and value is None:
                raise ValueError("core tag {} cannot be None".format(tag))

            if value is not None:
                if type(value) is not TagTypeMap[tag]:
                    raise ValueError('{} is not of type {}'.format(repr(value), TagTypeMap[tag]))
    except Exception as e:
        raise RuntimeError(
            "invalid metadata {}".format(extracted), e
        )
