"""utilities to sanity check the library"""
import os
import stat
from os import path
from os.path import join
from enum import Enum, auto
from unicodedata import is_normalized
from .metadata.core.alac import get_meta_data_alac
from .metadata.core.dsf import get_meta_data_dsf
from .metadata.core.sacdiso import get_meta_data_sacd_iso, get_total_tracks
from .metadata.core import check_valid_metadata
from .metadata.checksum import (
    get_checksum_in_24bit,
    check_valid_checksum_output,
    get_checksum_in_raw_stream,
    get_checksum_in_raw_file,
)
from .metadata.extra import (
    create_empty_extra_metadata,
    check_valid_extra_metadata
)

# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file?redirectedfrom=MSDN#file_and_directory_names
# having these characters in the filename is very bad for SMB network sharing and archiving.
INVALID_CHARACTERS = r'<>:*/\|?*'


class ScanType(Enum):
    CORE_METADATA = auto()
    CHECKSUM = auto()
    # ratings, comments, etc.
    EXTRA_METADATA = auto()


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


def fetch_cached_path_and_stat(result_cache, full_path):
    if result_cache is None:
        return

    data = result_cache.get(full_path, None)
    if data is None:
        return

    return data['path_and_stat']


def scan_one_directory(
        *, input_dir, aux_output_dir=None, result_cache=None,
        task: ScanType, ignore_dirs=None, overwrite_result_dict=None,
):
    """
    :param input_dir: directory path.
    :return:
    """

    check_valid_result = {
        ScanType.CORE_METADATA: check_valid_metadata,
        ScanType.CHECKSUM: check_valid_checksum_output,
        ScanType.EXTRA_METADATA: check_valid_extra_metadata,
    }[task]

    # our root dir should be properly named.
    assert is_normalized('NFD', input_dir)
    assert is_normalized('NFKD', input_dir)

    file_ct = 0
    folder_ct = 0
    warnings_all = []
    row_all = []
    path_and_stat_all = []
    extra_files_all = []

    for dirpath, dirnames, filenames in os.walk(input_dir):
        # check there is no invalid character
        for dir_component in dirpath.split(path.sep):
            assert valid_name(dir_component)

        assert is_normalized('NFD', dirpath)

        if not is_normalized('NFKD', dirpath):
            warnings_all.append(
                SanityCheckWarning(
                    WarningType.NON_NFKD_NAME,
                    join(input_dir, dirpath)
                )
            )

        # ignore this path if needed
        if (ignore_dirs is not None) and (join(input_dir, dirpath) in ignore_dirs):
            continue

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
            assert is_normalized('NFD', filename)

            # check more that there is not compatibility stuffs mixed in
            full_path = join(input_dir, dirpath, filename)
            if not is_normalized('NFKD', filename):
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

            ext_this = path.splitext(filename)[1]
            if fetch_cached_path_and_stat(result_cache, full_path) == p_and_stat:
                row_this = result_cache[full_path]['output']
            else:
                if task == ScanType.CORE_METADATA:
                    if ext_this == '.m4a':
                        row_this = get_meta_data_alac(full_path, aux_output_dir)
                    elif ext_this == '.dsf':
                        row_this = get_meta_data_dsf(full_path, aux_output_dir)
                    elif ext_this == '.iso':
                        row_this = get_meta_data_sacd_iso(
                            # sacd iso cannot embed image.
                            full_path, overwrite_result_dict
                        )
                    else:
                        extra_files_all.append(
                            full_path
                        )
                        continue
                elif task == ScanType.CHECKSUM:
                    if ext_this in {'.m4a'}:
                        row_this = get_checksum_in_24bit(full_path)
                    elif ext_this in {'.dsf'}:
                        row_this = get_checksum_in_raw_stream(full_path)
                    elif ext_this in {'.iso'}:
                        row_this = get_checksum_in_raw_file(full_path)
                    else:
                        extra_files_all.append(
                            full_path
                        )
                        continue
                elif task == ScanType.EXTRA_METADATA:
                    if ext_this == '.m4a':
                        row_this = overwrite_result_dict[full_path]
                    elif ext_this == '.dsf':
                        # just create empty rating.
                        row_this = create_empty_extra_metadata()
                    elif ext_this == '.iso':
                        # check how many tracks are there, and then create a list
                        row_this = [
                            create_empty_extra_metadata()
                        ] * get_total_tracks(full_path)
                    else:
                        extra_files_all.append(
                            full_path
                        )
                        continue
                else:
                    raise NotImplementedError

            try:
                check_valid_result(
                    row_this, ext_this
                )
            except Exception as e:
                raise ValueError(
                    f"invalid output from {repr(full_path)}",
                    e
                )

            row_all.append(row_this)
            path_and_stat_all.append(p_and_stat)

        if (folder_ct % 10 == 0) or (file_ct % 10 == 0):
            print(f'{folder_ct} folder scanned, {file_ct} files scanned')

    return {
        'folder_ct': folder_ct,
        'file_ct': file_ct,
        'warnings': warnings_all,
        'output': row_all,
        'path_and_stat': path_and_stat_all,
        'extra_files': extra_files_all,
        'input_dir': input_dir,
        'aux_output_dir': aux_output_dir,
        'task': task,
    }
