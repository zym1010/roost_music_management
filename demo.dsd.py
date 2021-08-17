from roost.scanner_wrapper import scan_one_dir
from roost.scanner import ScanType

input_dirs = [
    "/Volumes/Multimedia/DSD_Lib/Archived",
]

# you can define some `path` -> (partial) `output` mapping
# to overwrite the output extracted from files.
# it only works for SACD ISO, which is the only file format not editable.
# from dsd_overwrite import overwrite_result_dict
overwrite_result_dict = None


def check(task: ScanType):
    output_dir = task.name.lower()
    for dir_path in input_dirs:
        # parse the iTunes lib name from the full path.
        name_this = "all"
        print(name_this)
        scan_one_dir(
            input_dir=dir_path, output_dir=f'output_20210816_dsd_2/{name_this}/{output_dir}',
            task=task,
            ignore_dirs={
                # entires starting with this won't be checked.
                '/Volumes/Multimedia/DSD_Lib/Archived/DSD_Test/2019 5 Tracks in DSD512/NDSD013',
            },
            previous_output_dir=f'output_20210816_dsd/{name_this}/{output_dir}',
            overwrite_result_dict=overwrite_result_dict
        )


if __name__ == '__main__':
    # tested with Mutagen 1.45.1
    check(ScanType.CORE_METADATA)
    # check_again(ScanType.CORE_METADATA)

    # slow, needing FFmpeg. tested under 4.3.2
    check(ScanType.CHECKSUM)
    # check_again(ScanType.CHECKSUM)
