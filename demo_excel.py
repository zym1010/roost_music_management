# fetch all track info across all extracted JSONs,
# and then generate a huge excel file
# we can have two basic sheets
# 1. tracks
# 2. albums
# TODO
# 3. artists
# 4. album artists

# then we can have as many sheets as we like.
# basically smart playlists.
import pickle
import json
from os import path, walk
# tested with openpyxl 3.0.7
from openpyxl import Workbook
from roost.manager import AlbumManager, TrackManager, Track

PARENT_FOLDERS_TO_CHECK = [
    '/Users/yimengzh/Dropbox/music/output_20210806_with_mutagen/',
    '/Users/yimengzh/Dropbox/music/output_20210816_dsd/',
]


def get_all_libs():
    ret = []
    for parent_dir in PARENT_FOLDERS_TO_CHECK:
        for dirpath, dirnames, filenames in walk(parent_dir):
            if {'core_metadata', 'checksum', 'extra_metadata'} <= set(dirnames):
                ret.append(
                    path.join(parent_dir, dirpath)
                )

    return ret


def load_one_json(file_path):
    ret = dict()
    with open(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line_json = json.loads(line)
            path_this = line_json['path_and_stat']['path']
            output_this = line_json['output']
            assert path_this not in ret
            ret[path_this] = output_this
    return ret


def parse_one_lib(
        lib_dir,
        track_manager: TrackManager,
        album_manager: AlbumManager,
):
    # get main.json from core and aux metadata
    # generate two dicts
    core_json = path.join(lib_dir, 'core_metadata', 'main.json')
    extra_json = path.join(lib_dir, 'extra_metadata', 'main.json')

    # load each file
    core_dict = load_one_json(core_json)
    extra_dict = load_one_json(extra_json)
    assert core_dict.keys() == extra_dict.keys()

    for file_path in core_dict:
        output_core = core_dict[file_path]
        output_extra = extra_dict[file_path]
        assert type(output_extra) is type(output_core)
        if type(output_core) is dict:
            # then just add
            track = Track(
                file_path=file_path,
                core_metadata=output_core,
                extra_metadata=output_extra,
            )

            track_manager.add_track(track)
            album_manager.add_track(track)
        else:
            assert type(output_core) is list
            assert len(output_core) == len(output_extra)
            for idx, (output_core_this, output_extra_this) in enumerate(zip(
                    output_core, output_extra
            )):
                track = Track(
                    file_path=file_path,
                    subindex=idx,
                    core_metadata=output_core_this,
                    extra_metadata=output_extra_this,
                )
                track_manager.add_track(track)
                album_manager.add_track(track)


def main():
    track_manager = TrackManager()
    album_manager = AlbumManager()
    output = 'demo_excel.xlsx'
    for lib_dir in get_all_libs():
        print(lib_dir)
        parse_one_lib(lib_dir, track_manager, album_manager)

    print(len(track_manager.track_dict), 'tracks')
    print(len(album_manager.album_dict), 'albums')

    # save
    wb = Workbook(write_only=True)
    # dump album
    album_manager.export_to_sheet(wb.create_sheet('albums'))
    # dump track
    track_manager.export_to_sheet(wb.create_sheet('tracks'))

    # save
    wb.save(output)

    # dump two manaagers
    with open('demo_excel.pkl', 'wb') as f:
        pickle.dump(
            {
                'track_manager': track_manager,
                'album_manager': album_manager,
            }, f
        )


if __name__ == '__main__':
    main()
