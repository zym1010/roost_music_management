from hashlib import sha256
from os.path import exists, join

from mutagen.flac import FLAC, Picture

from .. import ExtractionError
from . import Tag


def fetch_one_field(
        tags: FLAC, field_name: str, converter, aux_output_dir: str,
):
    if field_name != 'PICTURE':
        data = tags.get(field_name, None)
    else:
        data = tags.pictures
        assert type(data) is list
        if len(data) == 0:
            data = None

    if data is None:
        return None

    assert type(data) is list and len(data) > 0
    if field_name == 'ARTIST':
        data = ['; '.join(data)]

    if len(data) != 1:
        raise ExtractionError(f"multiple values for field {repr(field_name)}")

    return converter(data[0], aux_output_dir)


def string_converter(data, _):
    assert type(data) is str
    if data == '':
        return None
    if data != data.strip():
        raise ExtractionError(f"{repr(data)} has spaces around")
    return data


def int_in_str_converter(data, _):
    assert type(data) is str
    if data == '':
        return None
    data_int = int(data)
    if str(data_int) != data:
        raise ValueError(f"{data} does not contain properly encoded int")
    return data_int


def cover_converter(data: Picture, output_dir):
    # compute the hash (sha256)
    hexdigest = sha256(data.data).hexdigest()
    # save the file.
    ext = {
        "image/jpeg": '.jpg',
        "image/png": '.png'
    }[data.mime]
    filename = hexdigest + ext

    fullpath = join(output_dir, filename)
    if not exists(fullpath):
        with open(fullpath, 'wb') as f:
            f.write(data.data)

    return filename


TAG_MAPPING_FLAC = {
    Tag.TITLE: ("TITLE", string_converter),
    Tag.ARTIST: ("ARTIST", string_converter),
    Tag.ALBUM: ("ALBUM", string_converter),
    Tag.ALBUM_ARTIST: ("ALBUMARTIST", string_converter),
    Tag.DISC_NO: ("DISCNUMBER", int_in_str_converter),
    Tag.DISC_TOTAL: ("DISCTOTAL", int_in_str_converter),
    Tag.YEAR: ("DATE", int_in_str_converter),
    Tag.TRACK_NO: ("TRACKNUMBER", int_in_str_converter),
    Tag.TRACK_TOTAL: ("TRACKTOTAL", int_in_str_converter),
    Tag.GENRE: ("GENRE", string_converter),
    Tag.COMPOSER: ("COMPOSER", string_converter),
    Tag.COVER_ART: ('PICTURE', cover_converter),
    # handle duration in another place.
}


def get_meta_data_flac(
        file_name_full,
        image_output_dir=None,
):
    flac_obj = FLAC(file_name_full)

    try:
        flac_info = flac_obj.info

        if flac_info.channels != 2:
            raise ExtractionError("number of channels is not 2", flac_info)
        if flac_info.bits_per_sample not in {16, 24}:
            raise ExtractionError("not 16 or 24 bit", flac_info)
        if flac_info.sample_rate not in {44100, 48000, 88200, 96000}:
            raise ExtractionError("invalid sample rate", flac_info)

        assert type(flac_info.length) is float

        if not (flac_info.length > 0):
            raise ExtractionError(f"audio length is not positive: {flac_info.length}")
        # print(flac_obj)
        ret = {
            k: fetch_one_field(flac_obj, field, func, image_output_dir) for k, (field, func) in TAG_MAPPING_FLAC.items()
        }

        ret[Tag.DURATION] = flac_info.length


    except Exception as e:
        raise ExtractionError(
            "encountered error processing {}".format(file_name_full), e
        )

    return ret
