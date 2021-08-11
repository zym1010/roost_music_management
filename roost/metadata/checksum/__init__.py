from subprocess import check_output

from enum import Enum, auto


class ChecksumType(Enum):
    PCM_S24LE = auto()
    RAW_STREAM = auto()


def get_checksum_in_24bit(file_name_full):
    # use ffmpeg to check raw audio stream's sha, converted to 24bit `pcm_s24le`
    # this is sufficient for pratically all non-DSD files.
    ffmpeg_output = check_output(
        [
            "/Users/yimengzh/miniconda3/envs/flask/bin/ffmpeg",
            "-i", file_name_full,
            "-vn",
            "-c:a", "pcm_s24le",
            "-f", "hash",
            "-hash", "sha256",
            "-"
        ]
    ).decode()

    dummy, result = ffmpeg_output.strip().split('=')
    assert dummy == 'SHA256'
    return {
        ChecksumType.PCM_S24LE: result,
    }


def get_checksum_in_raw_stream(file_name_full):
    # for DSD (non-ISO), use the original stream
    ffmpeg_output = check_output(
        [
            "/Users/yimengzh/miniconda3/envs/flask/bin/ffmpeg",
            "-i", file_name_full,
            "-vn",
            "-c:a", "copy",
            "-f", "hash",
            "-hash", "sha256",
            "-"
        ]
    ).decode()

    dummy, result = ffmpeg_output.strip().split('=')
    assert dummy == 'SHA256'
    return {
        ChecksumType.RAW_STREAM: result,
    }


def check_valid_checksum_output(output, ext):
    if ext in {'.m4a'}:
        assert output.keys() == {ChecksumType.PCM_S24LE}
    elif ext in {'.dsf'}:
        assert output.keys() == {ChecksumType.RAW_STREAM}
    else:
        raise ValueError
