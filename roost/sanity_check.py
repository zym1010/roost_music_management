"""utilities to sanity check the library"""
import os
import stat
from os import path
from os.path import join
from enum import Enum, auto
from unicodedata import normalize
from .metadata.extraction.alac import get_meta_data_alac
from .metadata import check_valid_metadata

# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file?redirectedfrom=MSDN#file_and_directory_names
# having these characters in the filename is very bad for SMB network sharing and archiving.
INVALID_CHARACTERS = r'<>:*/\|?*'


class WarningType(Enum):
    # file name is not in NFKD form.
    # not necessarily bad.
    NON_NFKD_NAME = auto()


class SanityCheckWarning:
    def __init__(self, warning_type: WarningType, message: str):
        assert type(warning_type) is WarningType
        assert type(message) is str
        self.warning_type = warning_type
        self.message = message

    def __repr__(self):
        return 'SanityCheckWarning(WarningType.{}, {})'.format(
            self.warning_type.name,
            repr(self.message)
        )


def valid_name(name):
    return check_no_bad_space(name) and valid_smb_name(name)


def check_no_bad_space(name):
    return (name.strip() == name) and '\n' not in name


def valid_smb_name(name):
    for c in INVALID_CHARACTERS:
        if c in name:
            return False
    return True


def fetch_cached_path_and_stat(metadata_cache, full_path):
    if metadata_cache is None:
        return

    data = metadata_cache.get(full_path, None)
    if data is None:
        return

    return data['path_and_stat']


def check_one_directory(root_dir, metadata_cache=None):
    """

    :param root_dir: directory path.
    :return:
    """

    # our root dir should be properly named.
    assert normalize('NFD', root_dir) == root_dir
    assert normalize('NFKD', root_dir) == root_dir

    file_ct = 0
    folder_ct = 0
    warnings_all = []
    metadata_all = []
    path_and_stat_all = []
    extra_files_all = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # check there is no invalid character
        for dir_component in dirpath.split(path.sep):
            assert valid_name(dir_component)

        assert normalize('NFD', dirpath) == dirpath

        if normalize('NFKD', dirpath) != dirpath:
            warnings_all.append(
                SanityCheckWarning(
                    WarningType.NON_NFKD_NAME,
                    join(root_dir, dirpath)
                )
            )

        for dirname in dirnames:
            assert valid_name(dirname)

        for filename in filenames:
            assert valid_name(filename)

        folder_ct += 1

        for filename in filenames:
            assert valid_name(filename)
            # ignore files starting with '.'
            if filename.startswith('.'):
                continue

            file_ct += 1

            # check that it's properly NFD
            # this is probably guaranteed by Samba or Finder.
            assert normalize('NFD', filename) == filename

            # check more that there is not compatibility stuffs mixed in
            full_path = join(root_dir, dirpath, filename)
            if normalize('NFKD', filename) != filename:
                warnings_all.append(
                    SanityCheckWarning(
                        WarningType.NON_NFKD_NAME,
                        full_path
                    )
                )

            p_and_stat = {
                'path': full_path,
                # this is guaranteed to be an integer.
                'mtime': os.stat(full_path)[stat.ST_MTIME],
                # this is guaranteed to be an integer.
                'size': os.stat(full_path)[stat.ST_SIZE]
            }

            if fetch_cached_path_and_stat(metadata_cache, full_path) == p_and_stat:
                metadata = metadata_cache[full_path]['metadata']
            else:
                ext_this = path.splitext(filename)[1]

                if ext_this == '.m4a':
                    metadata = get_meta_data_alac(full_path)
                else:
                    extra_files_all.append(
                        full_path
                    )
                    continue

            check_valid_metadata(
                metadata
            )

            metadata_all.append(metadata)
            path_and_stat_all.append(p_and_stat)

        if (folder_ct % 10 == 0) or (file_ct % 10 == 0):
            print(f'{folder_ct} folder scanned, {file_ct} files scanned')

    return {
        'folder_ct': folder_ct,
        'file_ct': file_ct,
        'warnings': warnings_all,
        'metadata': metadata_all,
        'path_and_stat': path_and_stat_all,
        'extra_files': extra_files_all,
    }
