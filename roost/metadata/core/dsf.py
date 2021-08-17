from hashlib import sha256
from os.path import exists, join

from mutagen.dsf import DSF
from mutagen.id3 import ID3Tags, APIC

from .. import ExtractionError
from . import Tag


def fetch_one_field(
        tags: ID3Tags, field_name: str, converter, aux_output_dir: str,
):
    data = tags.getall(field_name)
    assert type(data) is list
    if len(data) == 0:
        return None

    if len(data) != 1:
        raise ExtractionError(f"multiple values for field {repr(field_name)}")

    return converter(data[0], aux_output_dir)


def string_converter(data, _):
    data = data.text
    assert len(data) == 1
    data = data[0]
    assert type(data) is str
    if data == '':
        return None
    if data != data.strip():
        raise ExtractionError(f"{repr(data)} has spaces around")
    return data


def time_in_str_converter(data, _):
    data = data.text
    assert len(data) == 1
    data = data[0].get_text()
    assert type(data) is str
    if data == '':
        return None
    data_int = int(data)
    if str(data_int) != data:
        raise ValueError(f"{data} does not contain properly encoded int")
    return data_int


def tuple_converter(data, _):
    data = data.text
    assert len(data) == 1
    data = data[0]
    assert type(data) is str

    if "/" not in data:
        data1 = int(data)
        data2 = 0
    else:
        data1, data2 = data.split("/")
        data1 = int(data1)
        data2 = int(data2)

    assert type(data1) is int
    assert type(data2) is int
    if (data1 <= 0) or (data2 <= 0):
        raise ExtractionError(f"{repr(data)} has invalid (negative) numbers")
    return data1, data2


def cover_converter(data: APIC, output_dir):
    # compute the hash (sha256)
    hexdigest = sha256(bytes(data.data)).hexdigest()
    # save the file.
    ext = {
        'image/jpeg': '.jpg',
    }[data.mime]
    filename = hexdigest + ext

    fullpath = join(output_dir, filename)
    if not exists(fullpath):
        with open(fullpath, 'wb') as f:
            f.write(bytes(data.data))

    return filename


TAG_MAPPING_DSF = {
    Tag.TITLE: ("TIT2", string_converter),
    Tag.ARTIST: ("TPE1", string_converter),
    Tag.ALBUM: ("TALB", string_converter),
    Tag.ALBUM_ARTIST: ("TPE2", string_converter),
    Tag.DISC_NO: ("TPOS", lambda x, output_dir: tuple_converter(x, output_dir)[0]),
    Tag.DISC_TOTAL: ("TPOS", lambda x, output_dir: tuple_converter(x, output_dir)[1]),
    Tag.YEAR: ("TDRC", time_in_str_converter),
    Tag.TRACK_NO: ("TRCK", lambda x, output_dir: tuple_converter(x, output_dir)[0]),
    Tag.TRACK_TOTAL: ("TRCK", lambda x, output_dir: tuple_converter(x, output_dir)[1]),
    Tag.GENRE: ("TCON", string_converter),
    Tag.COMPOSER: ("TCOM", string_converter),
    Tag.COVER_ART: ('APIC', cover_converter),
    # handle duration in another place.
}


def get_meta_data_dsf(
        file_name_full,
        image_output_dir=None,
):
    dsf_obj = DSF(file_name_full)

    try:
        dsf_info = dsf_obj.info
        dsf_tags = dsf_obj.tags

        if dsf_info.channels != 2:
            raise ExtractionError("number of channels is not 2", dsf_info)
        if dsf_info.bits_per_sample != 1:
            raise ExtractionError("not 1 bit", dsf_info)
        if dsf_info.sample_rate not in {22579200, 11289600, 2822400, 5644800}:
            raise ExtractionError("invalid sample rate", dsf_info)

        assert type(dsf_info.length) is float

        if not (dsf_info.length > 0):
            raise ExtractionError(f"audio length is not positive: {dsf_info.length}")

        ret = {
            k: fetch_one_field(dsf_tags, field, func, image_output_dir) for k, (field, func) in TAG_MAPPING_DSF.items()
        }

        ret[Tag.DURATION] = dsf_info.length


    except Exception as e:
        raise ExtractionError(
            "encountered error processing {}".format(file_name_full), e
        )

    return ret
