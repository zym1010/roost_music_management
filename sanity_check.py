"""use roost.sanity_check to check the validity of existing music libraries"""
# tested under exiftool version 12.27
from roost import sanity_check


def check_my_lib():
    libs = [
        # each path should point to `Music` under your iTunes library folder.
        # for iTunes, that will mean something like
        # `/Users/USERNAME/Music/iTunes/iTunes\ Media/Music`
        # for Music in Catalina and later, that will mean something like
        # `/Users/USERNAME/Music/Music/Media.localized/Music`
        "/path/to/music/folder/under/your/itunes/lib",
        "/path/to/music/folder/under/your/another/itunes/lib",
    ]

    folder_ct = 0
    file_ct = 0
    warnings_all = []
    errors_all = []

    for lib in libs:
        print(lib)
        stats_this_lib = sanity_check.check_one_directory(lib, sanity_check.DirectoryProfile.ITUNES)
        folder_ct += stats_this_lib['folder_ct']
        file_ct += stats_this_lib['file_ct']
        warnings_all.extend(stats_this_lib['warnings'])
        errors_all.extend(stats_this_lib['errors'])

    print(f'{folder_ct} folders, {file_ct} files')
    print(f'{len(warnings_all)} warnings, {len(errors_all)} errors')
    print(errors_all)
    print(warnings_all)


if __name__ == '__main__':
    check_my_lib()
