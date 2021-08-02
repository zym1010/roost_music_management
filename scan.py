"""use roost.sanity_check to check the validity of existing music libraries"""
# tested under exiftool version 12.27
from os import makedirs
from os import path
from roost import sanity_check
import pickle
import json


def scan_dirs(*, input_dirs, output_dir, previous_output_dir=None):
    makedirs(output_dir, exist_ok=False)

    folder_ct = 0
    file_ct = 0
    warnings_all = []
    metadata_all = []
    path_and_stat_all = []
    extra_files_all = []

    # previous_output_dir is used to build a cache for metadata
    if previous_output_dir is not None:
        with open(path.join(previous_output_dir, 'full.pkl'), 'rb') as f_prev:
            data_prev = pickle.load(f_prev)
        # build using 'metadata' and 'path_and_stat'
        assert len(data_prev['path_and_stat']) == len(data_prev['metadata'])
        metadata_cache = {
            p_and_s_this['path']: {
                'path_and_stat': p_and_s_this,
                'metadata': mdata_this,
            } for (p_and_s_this, mdata_this) in zip(data_prev['path_and_stat'], data_prev['metadata'])
        }
    else:
        metadata_cache = None

    for input_dir in input_dirs:
        print(input_dir)
        stats_this_lib = sanity_check.check_one_directory(input_dir, metadata_cache=metadata_cache)
        folder_ct += stats_this_lib['folder_ct']
        file_ct += stats_this_lib['file_ct']
        warnings_all.extend(stats_this_lib['warnings'])
        extra_files_all.extend(stats_this_lib['extra_files'])
        metadata_all.extend(stats_this_lib['metadata'])
        path_and_stat_all.extend(stats_this_lib['path_and_stat'])

    print(f'{folder_ct} folders, {file_ct} files')
    print(f'{len(warnings_all)} warnings')

    # pickle version
    with open(path.join(output_dir, 'full.pkl'), 'wb') as f_pkl:
        pickle.dump(
            {
                'warnings': warnings_all,
                'extra_files': extra_files_all,
                'metadata': metadata_all,
                'path_and_stat': path_and_stat_all,
                'folder_ct': folder_ct,
                'file_ct': file_ct,
                'input_dirs': input_dirs,
            },
            f_pkl
        )
    # json version, aux
    with open(path.join(output_dir, 'aux.json'), 'wt', encoding='utf-8') as f_aux:
        json.dump(
            {
                'warnings': [repr(x) for x in warnings_all],
                'extra_files': extra_files_all,
                'folder_ct': folder_ct,
                'file_ct': file_ct,
                'input_dirs': input_dirs,
            },
            f_aux,
            indent=2,
            allow_nan=False,
        )

    # json version, path_stat_meta. one line at a time, to support scalable loading (if ever needed)
    assert len(metadata_all) == len(path_and_stat_all)
    with open(path.join(output_dir, 'path_stat_meta.json'), 'wt', encoding='utf-8') as f_path_stat_meta:
        for meta_this, path_and_stat_this in zip(metadata_all, path_and_stat_all):
            f_path_stat_meta.write(
                json.dumps(
                    {
                        'path_and_stat': {
                            # it has many large integers... good to save them as str.
                            k: str(v) for k, v in path_and_stat_this.items()
                        },
                        'metadata': {
                            # integers here won't be too big. so it's fine to encode them as is.
                            k.name: v for k, v in meta_this.items()
                        }
                    },
                    allow_nan=False,
                ) + '\n'
            )


def main():
    input_dirs = [
        "/Volumes/Multimedia/iTunes_Lib/Archived/My_Music_Library/Media.localized/Music",
        "/Volumes/Multimedia/iTunes_Lib/Archived/My_Music_Library_2/Media.localized/Music",
    ]
    for dir_path in input_dirs:
        name_this = dir_path.split('/')[5]
        print(name_this)
        scan_dirs(input_dirs=[dir_path], output_dir=f'output_20210801/{name_this}/from_files')


def main_check_again():
    input_dirs = [
        "/Volumes/Multimedia/iTunes_Lib/Archived/My_Music_Library/Media.localized/Music",
        "/Volumes/Multimedia/iTunes_Lib/Archived/My_Music_Library_2/Media.localized/Music",
    ]

    for dir_path in input_dirs:
        name_this = dir_path.split('/')[5]
        print(name_this)
        scan_dirs(
            input_dirs=[dir_path], output_dir=f'output_20210801_again/{name_this}/from_files',
            previous_output_dir=f'output_20210801/{name_this}/from_files',
        )


if __name__ == '__main__':
    # main()
    main_check_again()