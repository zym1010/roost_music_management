from roost.scanner_wrapper import scan_one_dir
from roost.scanner import ScanType

input_dirs = [
    "/Volumes/Multimedia/DSD_Lib/Archived",
]


def check(task: ScanType):
    output_dir = task.name.lower()
    for dir_path in input_dirs:
        # parse the iTunes lib name from the full path.
        name_this = "all"
        print(name_this)
        scan_one_dir(
            input_dir=dir_path, output_dir=f'output_20210810_dsd/{name_this}/{output_dir}',
            task=task,
            ignore_dirs={
                '/Volumes/Multimedia/DSD_Lib/Archived/DSD_Test/2019 5 Tracks in DSD512/NDSD013',
            }
        )


if __name__ == '__main__':
    # tested with Mutagen 1.45.1
    check(ScanType.CORE_METADATA)
    # check_again(ScanType.CORE_METADATA)

    # slow, needing FFmpeg. tested under 4.3.2
    # check(ScanType.CHECKSUM)
    # check_again(ScanType.CHECKSUM)
