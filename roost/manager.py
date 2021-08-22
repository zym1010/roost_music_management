from unicodedata import normalize
# tested with openpyxl 3.0.7
from openpyxl.worksheet.worksheet import Worksheet
from typing import List
from itertools import groupby


class Track:
    def __init__(self, *, file_path: str, subindex=-1, core_metadata: dict, extra_metadata: dict):
        self.file_path = file_path
        self.subindex = subindex
        self.core_metadata = core_metadata

        for k in self.core_metadata:
            if type(self.core_metadata[k]) is str:
                self.core_metadata[k] = normalize('NFC', self.core_metadata[k])

        self.extra_metadata = extra_metadata

        for k in self.extra_metadata:
            if type(self.extra_metadata[k]) is str:
                self.extra_metadata[k] = normalize('NFC', self.extra_metadata[k])

    @property
    def album_key(self):
        return self.core_metadata['ALBUM_ARTIST'], self.core_metadata['ALBUM']

    @property
    def track_key(self):
        return (self.file_path, self.subindex)


class TrackManager:
    def __init__(self):
        self.track_dict = dict()
        self.id_to_key = dict()

    def add_track(self, track):
        assert track.track_key not in self.track_dict
        new_id = len(self.track_dict)
        self.track_dict[track.track_key] = {
            'id': new_id,
            'track': track,
        }
        assert new_id not in self.id_to_key
        self.id_to_key[new_id] = track.track_key

    def export_to_sheet(self, sheet: Worksheet):
        demo_track: Track = next(iter(self.track_dict.values()))['track']
        keys_core = sorted(demo_track.core_metadata.keys())
        keys_meta = sorted(demo_track.extra_metadata.keys())
        header = ['id'] + keys_core + keys_meta
        sheet.append(header)
        for key, v in self.track_dict.items():
            track = v['track']
            row_core = [
                track.core_metadata[x] for x in keys_core
            ]
            row_extra = [
                track.extra_metadata[x] for x in keys_meta
            ]
            row_this = [v['id']] + row_core + row_extra
            sheet.append(row_this)


class AlbumManager:
    def __init__(self):
        # disambiguate albums using raw album  name + album artist
        self.album_dict = dict()
        self.id_to_key = dict()

    def add_track(self, track: Track):
        key = track.album_key
        if key not in self.album_dict:
            new_id = len(self.album_dict)
            self.album_dict[key] = {
                'id': new_id,
                'tracks': [],
            }
            assert new_id not in self.id_to_key
            self.id_to_key[new_id] = key

        self.album_dict[key]['tracks'].append(track)

    def check_album_consistency(self, tracks: List[Track]):
        try:
            disc_total_this = tracks[0].core_metadata['DISC_TOTAL']
            year_this = tracks[0].core_metadata['YEAR']
            genre_this = tracks[0].core_metadata['GENRE']

            tracks = sorted(tracks, key=lambda x: (x.core_metadata['DISC_NO'], x.core_metadata['TRACK_NO']))
            disc_no_all = []
            for disc_no, g in groupby(tracks, lambda x: x.core_metadata['DISC_NO']):
                g_to_use = list(g)
                assert 1 <= disc_no <= disc_total_this
                track_total_this = g_to_use[0].core_metadata['TRACK_TOTAL']

                for track_this in g_to_use:
                    assert track_this.core_metadata['TRACK_TOTAL'] == track_total_this
                    assert track_this.core_metadata['DISC_TOTAL'] == disc_total_this
                    assert track_this.core_metadata['YEAR'] == year_this, (track_this.core_metadata, year_this)
                    assert track_this.core_metadata['GENRE'] == genre_this
                assert [x.core_metadata['TRACK_NO'] for x in g_to_use] == list(range(1, track_total_this + 1))
                disc_no_all.append(disc_no)

            assert len(disc_no_all) == len(set(disc_no_all))
            assert set(disc_no_all) <= set(range(1, disc_total_this + 1))
            assert disc_no_all == list(range(1, disc_total_this + 1))
            return True
        except Exception:
            return False

    def export_to_sheet(self, sheet: Worksheet):
        sheet.append(
            ['id', 'ALBUM_ARTIST', 'ALBUM', 'TRACKS', 'CONSISTENT']
        )
        for key, v in self.album_dict.items():
            row_this = [v['id'], key[0], key[1], len(v['tracks'])]

            # check if it's well behaved.
            #
            row_this.append(
                self.check_album_consistency(v['tracks'])
            )

            sheet.append(row_this)
