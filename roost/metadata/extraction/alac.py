from .. import Tag
from . import extract_meta

QTItemListPrefix = '{http://ns.exiftool.org/QuickTime/ItemList/1.0/}'  # noqa
TAG_AUDIO_FORMAT = '{http://ns.exiftool.org/QuickTime/Track1/1.0/}AudioFormat'  # noqa
TAG_DURATION = '{http://ns.exiftool.org/QuickTime/Track1/1.0/}MediaDuration'  # noqa
TAG_CHANNEL = '{http://ns.exiftool.org/QuickTime/Track1/1.0/}AudioChannels'  # noqa

TAG_MAPPING_ALAC = {
    Tag.TITLE: f"{QTItemListPrefix}Title",
    Tag.ARTIST: f"{QTItemListPrefix}Artist",
    Tag.ALBUM: f"{QTItemListPrefix}Album",
    Tag.ALBUM_ARTIST: f"{QTItemListPrefix}AlbumArtist",
    Tag.DISC_NO: f"{QTItemListPrefix}DiskNumber",
    Tag.DISC_TOTAL: f"{QTItemListPrefix}DiskNumber",
    Tag.YEAR: f"{QTItemListPrefix}ContentCreateDate",
    Tag.TRACK_NO: f"{QTItemListPrefix}TrackNumber",
    Tag.TRACK_TOTAL: f"{QTItemListPrefix}TrackNumber",
    Tag.GENRE: f"{QTItemListPrefix}Genre",
    Tag.COMPOSER: f"{QTItemListPrefix}Composer",
    Tag.DURATION: TAG_DURATION,
}

TAG_TO_CHECK = set(TAG_MAPPING_ALAC.values()) | {
    TAG_AUDIO_FORMAT, TAG_CHANNEL
}


def get_meta_data_alac(
        file_name_full
):
    xml_output = extract_meta(file_name_full)

    xml_ret = dict()

    try:
        for element in xml_output.iter():
            if element.tag in TAG_TO_CHECK:
                if element.tag in xml_ret:
                    raise RuntimeError(
                        "tag {} is duplicated".format(
                            element.tag
                        )
                    )
                if element.text is None:
                    # it's fine to have None data.
                    # raise RuntimeError(
                    #     "tag {} has bad data (None)".format(
                    #         element.tag
                    #     )
                    # )
                    pass
                else:
                    if ((element.text != element.text.strip()) or (len(element.text) == 0)):
                        raise RuntimeError(
                            "tag {} has bad data (empty or with trailing/tailing spaces) {}".format(
                                element.tag, repr(element.text)
                            )
                        )

                xml_ret[element.tag] = element.text

        if xml_ret[TAG_AUDIO_FORMAT] != 'alac':
            raise ValueError("audio format is not ALAC")
        if xml_ret[TAG_CHANNEL] != '2':
            raise ValueError("number of channels is not 2")

        ret = {k: xml_ret.get(v, None) for k, v in TAG_MAPPING_ALAC.items()}

        track_no_str, track_total_str = ret[Tag.TRACK_NO].split("of")
        track_no = int(track_no_str)
        track_total = int(track_total_str)
        if str(track_no) + ' ' != track_no_str:
            raise ValueError("improper track number")
        if ' ' + str(track_total) != track_total_str:
            raise ValueError("improper total track number")
        ret[Tag.TRACK_NO] = track_no
        ret[Tag.TRACK_TOTAL] = track_total

        disc_no_str, disc_total_str = ret[Tag.DISC_NO].split("of")
        disc_no = int(disc_no_str)
        disc_total = int(disc_total_str)
        if str(disc_no) + ' ' != disc_no_str:
            raise ValueError("improper disc number")
        if ' ' + str(disc_total) != disc_total_str:
            raise ValueError("improper total disc number")
        ret[Tag.DISC_NO] = disc_no
        ret[Tag.DISC_TOTAL] = disc_total

        year_str = ret[Tag.YEAR]
        year = int(year_str)
        if str(year) != year_str:
            raise ValueError("improper year")
        ret[Tag.YEAR] = year

        duration_in_sec = float(ret[Tag.DURATION])
        assert duration_in_sec > 0
        ret[Tag.DURATION] = duration_in_sec

        return ret
    except Exception as e:
        raise RuntimeError(
            "encountered error processing {}".format(file_name_full), e, xml_ret
        )
