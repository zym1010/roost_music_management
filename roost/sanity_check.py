"""utilities to sanity check the library"""
import os
from os import path
from os.path import join
from enum import Enum, auto
from unicodedata import normalize
from .metadata.extraction.alac import get_meta_data_alac
from .metadata import check_valid_metadata

# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file?redirectedfrom=MSDN#file_and_directory_names
# having these characters in the filename is very bad for SMB network sharing and archiving.
INVALID_CHARACTERS = r'<>:*/\|?*'


class DirectoryProfile(Enum):
    ITUNES = auto()


class WarningType(Enum):
    # file name is not in NFKD form.
    # not necessarily bad.
    NON_NFKD_NAME = auto()


class ErrorType(Enum):
    # tags we care about
    # (title, track, year, artist, album artist, disc, composer) is not unique
    NON_UNIQUE_TAGS = auto()
    # any of (title, track, year, artist, album artist, disc, composer) is missing or not in expected format.
    CORE_TAGS_BROKEN = auto()


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


class SanityCheckError:
    def __init__(self, error_type: ErrorType, message: str):
        assert type(error_type) is ErrorType
        assert type(message) is str
        self.error_type = error_type
        self.message = message

    def __repr__(self):
        return 'SanityCheckError(ErrorType.{}, {})'.format(
            self.error_type.name,
            repr(self.message)
        )


def valid_smb_name(name):
    for c in INVALID_CHARACTERS:
        if c in name:
            return False
    return True


def check_one_directory(root_dir, profile: DirectoryProfile):
    """

    :param root_dir: directory path.
    :param profile: what kind of directory is being processed.
        * ITUNES: it should be the `Music` folder under `Media`/`iTunes Media`. It should contain
                  ONLY .m4a files and no file of any other extension.
    :return:
    """

    # our root dir should be properly named.
    assert normalize('NFD', root_dir) == root_dir
    assert normalize('NFKD', root_dir) == root_dir

    assert profile == DirectoryProfile.ITUNES
    file_ct = 0
    folder_ct = 0
    errors_all = []
    warnings_all = []
    metadata_all = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # check there is no invalid character
        for dir_component in dirpath.split(path.sep):
            assert valid_smb_name(dir_component)

        assert normalize('NFD', dirpath) == dirpath

        if normalize('NFKD', dirpath) != dirpath:
            warnings_all.append(
                Warning(
                    WarningType.NON_NFKD_NAME,
                    join(root_dir, dirpath)
                )
            )

        for dirname in dirnames:
            assert valid_smb_name(dirname)

        for filename in filenames:
            assert valid_smb_name(filename)

        folder_ct += 1

        for filename in filenames:
            assert valid_smb_name(filename)
            # ignore files starting with '.'
            if filename.startswith('.'):
                continue

            file_ct += 1

            assert path.splitext(filename)[1] == '.m4a'

            # check that it's properly NFD
            # this is probably guaranteed by Samba or Finder.
            assert normalize('NFD', filename) == filename

            # check more that there is not compatibility stuffs mixed in
            if normalize('NFKD', filename) != filename:
                warnings_all.append(
                    Warning(
                        WarningType.NON_NFKD_NAME,
                        join(root_dir, dirpath, filename)
                    )
                )

            metadata = get_meta_data_alac(join(root_dir, dirpath, filename))

            check_valid_metadata(
                metadata
            )

            metadata_all.append(metadata)

        if (folder_ct % 10 == 0) or (file_ct % 10 == 0):
            print(f'{folder_ct} folder scanned, {file_ct} files scanned')

    return {
        'folder_ct': folder_ct,
        'file_ct': file_ct,
        'errors': errors_all,
        'warnings': warnings_all,
        'metadata': metadata_all,
    }
