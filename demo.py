from os.path import join
from roost.scanner_wrapper import scan_one_dir
from roost.scanner import ScanType
from roost.metadata.extra import convert_itunes_xml

input_dirs = [
    # in this demo, they are Music app's directories.
    "/Volumes/Multimedia/iTunes_Lib/Archived/Music_Classical_Beethoven/Media.localized/Music",
    "/Volumes/Multimedia/iTunes_Lib/Archived/Music_Classical_Bach/Media.localized/Music",
]


def check(task: ScanType):
    output_dir = task.name.lower()
    for dir_path in input_dirs:
        # parse the iTunes lib name from the full path.
        name_this = dir_path.split('/')[5]
        if task == ScanType.EXTRA_METADATA:
            overwrite_result_dict = convert_itunes_xml(
                join(dir_path, '..', '..', 'Library.xml')
            )
        else:
            overwrite_result_dict = None
        print(name_this)
        scan_one_dir(
            input_dir=dir_path, output_dir=f'output_20210806_with_mutagen/{name_this}/{output_dir}',
            task=task,
            overwrite_result_dict=overwrite_result_dict
        )


def check_again(task: ScanType):
    output_dir = task.name.lower()
    for dir_path in input_dirs:
        # parse the iTunes lib name from the full path.
        name_this = dir_path.split('/')[5]
        print(name_this)
        scan_one_dir(
            input_dir=dir_path, output_dir=f'output_20210806_with_mutagen_again/{name_this}/{output_dir}',
            task=task,
            previous_output_dir=f'output_20210806_with_mutagen/{name_this}/{output_dir}',
        )


if __name__ == '__main__':
    # tested with Mutagen 1.45.1
    # check(ScanType.CORE_METADATA)
    check_again(ScanType.CORE_METADATA)

    # slow, needing FFmpeg. tested under 4.3.2
    # check(ScanType.CHECKSUM)
    check_again(ScanType.CHECKSUM)
    # check(ScanType.EXTRA_METADATA)
    check_again(ScanType.EXTRA_METADATA)
