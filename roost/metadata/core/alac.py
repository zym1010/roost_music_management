from hashlib import sha256
from os.path import exists, join

from mutagen.mp4 import MP4, MP4Tags, MP4Cover

from .. import ExtractionError
from . import Tag


def fetch_one_field(
        tags: MP4Tags, field_name: str, converter, aux_output_dir: str,
):
    data = tags.get(field_name, None)
    if data is None:
        return None

    assert type(data) is list
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


def tuple_converter(data, _):
    assert type(data) is tuple
    assert len(data) == 2
    data1, data2 = data
    assert type(data1) is int
    assert type(data2) is int
    if (data1 <= 0) or (data2 <= 0):
        raise ExtractionError(f"{repr(data)} has invalid (negative) numbers")
    return data1, data2


def cover_converter(data: MP4Cover, output_dir):
    # compute the hash (sha256)
    hexdigest = sha256(bytes(data)).hexdigest()
    # save the file.
    ext = {
        data.FORMAT_PNG: '.png',
        data.FORMAT_JPEG: '.jpg'
    }[data.imageformat]
    filename = hexdigest + ext

    fullpath = join(output_dir, filename)
    if not exists(fullpath):
        with open(fullpath, 'wb') as f:
            f.write(bytes(data))

    return filename


TAG_MAPPING_ALAC = {
    Tag.TITLE: ("\xa9nam", string_converter),
    Tag.ARTIST: ("\xa9ART", string_converter),
    Tag.ALBUM: ("\xa9alb", string_converter),
    Tag.ALBUM_ARTIST: ("aART", string_converter),
    Tag.DISC_NO: ("disk", lambda x, output_dir: tuple_converter(x, output_dir)[0]),
    Tag.DISC_TOTAL: ("disk", lambda x, output_dir: tuple_converter(x, output_dir)[1]),
    Tag.YEAR: ("\xa9day", int_in_str_converter),
    Tag.TRACK_NO: ("trkn", lambda x, output_dir: tuple_converter(x, output_dir)[0]),
    Tag.TRACK_TOTAL: ("trkn", lambda x, output_dir: tuple_converter(x, output_dir)[1]),
    Tag.GENRE: ("\xa9gen", string_converter),
    Tag.COMPOSER: ("\xa9wrt", string_converter),
    Tag.COVER_ART: ('covr', cover_converter),
    # handle duration in another place.
}


def get_meta_data_alac(
        file_name_full,
        image_output_dir=None,
):
    mp4_obj = MP4(file_name_full)

    try:
        mp4_info = mp4_obj.info
        mp4_tags = mp4_obj.tags

        if mp4_info.codec != 'alac':
            raise ExtractionError("audio format is not ALAC", mp4_info)
        if mp4_info.channels != 2:
            raise ExtractionError("number of channels is not 2", mp4_info)
        if mp4_info.bits_per_sample not in {16, 24}:
            raise ExtractionError("not 16 or 24 bit", mp4_info)
        if mp4_info.sample_rate not in {44100, 48000, 88200, 96000}:
            raise ExtractionError("invalid sample rate", mp4_info)

        assert type(mp4_info.length) is float

        if not (mp4_info.length > 0):
            raise ExtractionError(f"audio length is not positive: {mp4_info.length}")

        ret = {
            k: fetch_one_field(mp4_tags, field, func, image_output_dir) for k, (field, func) in TAG_MAPPING_ALAC.items()
        }

        ret[Tag.DURATION] = mp4_info.length


    except Exception as e:
        raise ExtractionError(
            "encountered error processing {}".format(file_name_full), e
        )

    return ret
