import json
import pickle
from enum import Enum
from os import makedirs
from os import path

from . import scanner
from .metadata.checksum import ChecksumType
from .metadata.core import Tag
from .metadata.extra import Extra

task_to_enum_map = {
    scanner.ScanType.CORE_METADATA: Tag,
    scanner.ScanType.CHECKSUM: ChecksumType,
    scanner.ScanType.EXTRA_METADATA: Extra,
}


def decode_output(enum_to_use, output):
    if type(output) is dict:
        return {getattr(enum_to_use, k): v for k, v in output.items()}
    elif type(output) is list:
        return [decode_output(enum_to_use, x) for x in output]
    else:
        raise TypeError


def encode_output(output):
    if type(output) is dict:
        return {k.name: v for k, v in output.items()}
    elif type(output) is list:
        return [encode_output(x) for x in output]
    else:
        raise TypeError


def scan_one_dir(
        *, input_dir, output_dir, previous_output_dir=None, task, ignore_dirs=None,
        overwrite_result_dict=None, update_multi_value_fields=False,
):
    makedirs(output_dir, exist_ok=False)
    if task == scanner.ScanType.CORE_METADATA:
        aux_output_dir = path.join(output_dir, 'images')
        makedirs(aux_output_dir, exist_ok=False)
    else:
        aux_output_dir = None

    # previous_output_dir is used to build a cache for metadata
    if previous_output_dir is not None:
        result_cache = dict()
        enum_to_use: Enum = task_to_enum_map[task]
        with open(path.join(previous_output_dir, 'main.json'), 'rt') as f_prev:
            for line_this in f_prev:
                json_this = json.loads(line_this)
                json_this['output'] = decode_output(enum_to_use, json_this['output'])
                json_this['path_and_stat'] = {
                    k: (int(v) if k != 'path' else v) for k, v in json_this['path_and_stat'].items()
                }
                result_cache[json_this['path_and_stat']['path']] = json_this
    else:
        result_cache = None

    print(input_dir)
    stats_this_lib = scanner.scan_one_directory(
        input_dir=input_dir,
        result_cache=result_cache,
        task=task,
        aux_output_dir=aux_output_dir,
        ignore_dirs=ignore_dirs,
        overwrite_result_dict=overwrite_result_dict,
        update_multi_value_fields=update_multi_value_fields,
    )

    print(f'{stats_this_lib["folder_ct"]} folders, {stats_this_lib["file_ct"]} files')
    print(f'{len(stats_this_lib["warnings"])} warnings')

    assert stats_this_lib.keys() == {
        'folder_ct',
        'file_ct',
        'warnings',
        'output',
        'path_and_stat',
        'extra_files',
        'input_dir',
        'aux_output_dir',
        'task',
    }

    # this is useful for iTunes library where we don't expect to have any extra files.
    # pls turn this off when dealing with non-iTunes libraries
    assert len(stats_this_lib['extra_files']) == 0, 'no extra file'

    # pickle version
    with open(path.join(output_dir, 'full.pkl'), 'wb') as f_pkl:
        pickle.dump(
            stats_this_lib,
            f_pkl
        )
    # json version, aux
    with open(path.join(output_dir, 'aux.json'), 'wt', encoding='utf-8') as f_aux:
        json.dump(
            {
                'warnings': [repr(x) for x in stats_this_lib["warnings"]],
                'extra_files': stats_this_lib["extra_files"],
                'folder_ct': stats_this_lib["folder_ct"],
                'file_ct': stats_this_lib["file_ct"],
                'input_dir': stats_this_lib["input_dir"],
                'aux_output_dir': stats_this_lib["aux_output_dir"],
                "task": stats_this_lib["task"].name
            },
            f_aux,
            indent=2,
            allow_nan=False,
        )

    # json version, path_stat_meta. one line at a time, to support scalable loading (if ever needed)
    output_all = stats_this_lib['output']
    path_and_stat_all = stats_this_lib['path_and_stat']
    assert len(output_all) == len(path_and_stat_all)
    with open(path.join(output_dir, 'main.json'), 'wt', encoding='utf-8') as f_path_stat_meta:
        for row_this, path_and_stat_this in zip(output_all, path_and_stat_all):
            f_path_stat_meta.write(
                json.dumps(
                    {
                        'path_and_stat': {
                            # it has many large integers... good to save them as str.
                            k: str(v) for k, v in path_and_stat_this.items()
                        },
                        'output': encode_output(row_this)
                    },
                    allow_nan=False,
                ) + '\n'
            )
