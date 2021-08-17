from os.path import join, isabs, splitext, dirname
from os import walk
from subprocess import check_call
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from .. import ExtractionError
from . import Tag

from ... import BIN_SACDEXTRACT


def fetch_sacd_xml(
        full_name_full,
):
    with TemporaryDirectory() as tmp_dir:
        assert isabs(tmp_dir)
        check_call(
            [
                BIN_SACDEXTRACT,
                "--print",
                "--export-cue",
                f"--input={full_name_full}",
                f"--output-dir={tmp_dir}",
            ],
            cwd=dirname(BIN_SACDEXTRACT),
        )
        # then let's walk the tree and find the first xml file
        for dirpath, dirnames, filenames in walk(tmp_dir):
            for file_this in filenames:
                if splitext(file_this)[1] == '.xml':
                    return ElementTree.parse(
                        join(tmp_dir, dirpath, file_this)
                    )

    raise ExtractionError('cannot extract')


def string_converter(x):
    return x.strip()


def int_converter(x):
    return int(x)


def duration_converter(x):
    mm, ss, ff = x.split(":")
    # each second has 75 frames in Red Book
    return float(int(mm) * 60 + int(ss) + int(ff) / 75)


TAG_MAPPING_SACDISO = {
    Tag.TITLE: ("TITLE", string_converter),
    Tag.ARTIST: ("PERFORMER", string_converter),
    Tag.ALBUM: ("ALBUM", string_converter),
    Tag.ALBUM_ARTIST: ("ALBUM ARTIST", string_converter),
    Tag.YEAR: ("DATE", int_converter),
    Tag.TRACK_NO: ("TRACKNUMBER", int_converter),
    Tag.TRACK_TOTAL: ("TOTALTRACKS", int_converter),
    Tag.GENRE: ("GENRE", string_converter),
    Tag.COMPOSER: ("COMPOSER", string_converter),
    # handle duration in another place.
    Tag.DURATION: ("Duration", duration_converter),
}


def fetch_one_field(
        tags: dict, field_name: str, converter,
):
    data = tags.get(field_name, None)

    if data is None:
        return None

    assert type(data) is str
    return converter(data)


def fetch_album_and_area(xml_obj):
    album = None
    area = None
    for x in xml_obj.iter():
        if x.tag == 'Album':
            assert album is None
            album = x

        if x.tag == 'Area' and x.attrib['speaker_configuration'] == '2 Channel':
            assert area is None
            area = x
    assert album is not None, "album tag does not exist"
    assert area is not None, "area tag does not exist"
    return album, area


def get_total_tracks(file_name_full):
    xml_obj = fetch_sacd_xml(file_name_full)
    album, area = fetch_album_and_area(xml_obj)
    total_tracks = int(area.attrib['totaltracks'])
    assert len(area) == total_tracks
    return total_tracks


def get_meta_data_sacd_iso(
        file_name_full,
        overwrite_result_dict=None,
):
    try:
        xml_obj = fetch_sacd_xml(file_name_full)
        album, area = fetch_album_and_area(xml_obj)
        total_tracks = int(area.attrib['totaltracks'])
        assert len(area) == total_tracks
        ret = []
        for track_tag_this in area:
            metas_all = list(track_tag_this)
            metas_all = {d.attrib["name"]: d.attrib["value"] for d in metas_all}
            ret_track_this = {
                k: fetch_one_field(
                    metas_all, field, func
                ) for k, (field, func) in TAG_MAPPING_SACDISO.items()
            }

            ret_track_this.update({
                Tag.DISC_TOTAL: int(album.attrib['set_size']),
                Tag.DISC_NO: int(album.attrib['sequence_number']),
                Tag.COVER_ART: None,
            })
            ret.append(ret_track_this)

        if overwrite_result_dict is not None and file_name_full in overwrite_result_dict:
            overwrite_result = overwrite_result_dict[file_name_full]
            assert type(overwrite_result) is list
            assert len(overwrite_result) == total_tracks == len(ret)
            for ret_track_extracted, overwrite_track in zip(ret, overwrite_result):
                ret_track_extracted.update(overwrite_track)

    except Exception as e:
        raise ExtractionError(
            "encountered error processing {}".format(file_name_full), e
        )

    return ret
