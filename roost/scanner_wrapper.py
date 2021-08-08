from os import makedirs
from os import path
from . import scanner
import pickle
import json


def scan_one_dir(*, input_dir, output_dir, previous_output_dir=None, task):
    makedirs(output_dir, exist_ok=False)
    if task == scanner.ScanType.CORE_METADATA:
        aux_output_dir = path.join(output_dir, 'images')
        makedirs(aux_output_dir, exist_ok=False)
    else:
        aux_output_dir = None

    # previous_output_dir is used to build a cache for metadata
    if previous_output_dir is not None:
        with open(path.join(previous_output_dir, 'full.pkl'), 'rb') as f_prev:
            data_prev = pickle.load(f_prev)
        # build using 'output' and 'path_and_stat'
        assert len(data_prev['path_and_stat']) == len(data_prev['output'])
        result_cache = {
            p_and_s_this['path']: {
                'path_and_stat': p_and_s_this,
                'output': output_this,
            } for (p_and_s_this, output_this) in zip(data_prev['path_and_stat'], data_prev['output'])
        }
    else:
        result_cache = None

    print(input_dir)
    stats_this_lib = scanner.scan_one_directory(
        input_dir=input_dir,
        result_cache=result_cache,
        task=task,
        aux_output_dir=aux_output_dir,
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
                        'output': {
                            # integers here won't be too big. so it's fine to encode them as is.
                            # TODO: make sure this is fine for any task
                            k.name: v for k, v in row_this.items()
                        }
                    },
                    allow_nan=False,
                ) + '\n'
            )
