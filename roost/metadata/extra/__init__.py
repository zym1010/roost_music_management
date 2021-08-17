from enum import Enum, auto
from unicodedata import is_normalized
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

                if type(value) is str:
                    assert value != ''
                    assert value == value.strip()
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
