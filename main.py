import json
import math
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set
import argparse

from vosk import Model, KaldiRecognizer, SetLogLevel

SAMPLING_RATE = 16000


@dataclass
class Interval:
    start: float
    end: float


@dataclass
class Sentence:
    text: str
    interval: Interval


def format_time(f: float) -> str:
    h = int(f // 3600)
    f -= h * 3600
    m = int(f // 60)
    f -= m * 60
    s = math.floor(f)
    f -= s
    ms = int(1000 * f)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


class VideoCutter:
    def __init__(self, video_path: Path, sampling_rate: int = SAMPLING_RATE,
                 ):
        self._video_path = video_path
        self._sampling_rate = sampling_rate
        self._wav_path = self._video_path.with_suffix(".wav")
        self._txt_path = self._video_path.with_suffix(".txt")
        self._time_path = self._video_path.with_suffix(".time")
        self._list_path = self._video_path.parent / "list.txt"
        self._out_path = self._video_path.parent / (
                self._video_path.stem + "-out" + self._video_path.suffix)

    def extract_text(self, model="models/fr"):
        SetLogLevel(0)
        self._convert_to_wav()
        duration = self._get_video_duration()
        sentences = self._extract_sentences(model, duration)
        self._write_text(sentences)
        self._write_time(sentences)
        print("Please edit file {} before assembling.".format(self._txt_path))

    def _convert_to_wav(self):
        self._execute([
            "ffmpeg", "-y", "-loglevel", "quiet", "-i", str(self._video_path),
            "-ar", str(self._sampling_rate), "-ac", "1", str(self._wav_path)
        ])

    def _get_video_duration(self) -> float:
        ret = self._execute([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(self._video_path)
        ])
        duration_str = ret.stdout.decode('utf-8').strip()
        return float(duration_str)

    def _extract_sentences(self, model: str, duration: float) -> List[Sentence]:
        wf = wave.open(str(self._wav_path), "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise ValueError()
        model = Model(model)
        rec = KaldiRecognizer(model, self._sampling_rate)
        rec.SetWords(True)  # to get the timestamps
        sentences = []
        end = 0.0
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                try:
                    words = result['result']
                    start = words[0]["start"]
                    end = words[-1]["end"]
                    text = result["text"]
                    sentences.append(Sentence(text, Interval(start, end)))
                except KeyError:
                    pass
        result = json.loads(rec.FinalResult())
        try:
            text = result["partial"]
        except KeyError:
            pass
        else:
            sentences.append(Sentence(text, Interval(end, duration)))
        return sentences

    def _write_time(self, sentences: List[Sentence]):
        with self._time_path.open("w", encoding="utf-8") as d:
            for i, sentence in enumerate(sentences, 1):
                interval = sentence.interval
                d.write(f"{i}/{interval.start}/{interval.end}\n")

    def _write_text(self, sentences: List[Sentence]):
        with self._txt_path.open("w", encoding="utf-8") as d:
            for i, sentence in enumerate(sentences, 1):
                d.write(f"{i}/ {sentence.text}\n")

    def assemble(self):
        nums = self._get_selected_nums()
        intervals = self._get_selected_intervals(nums)
        merged_intervals = self._merge_intervals(intervals)
        merged_intervals = [Interval(interval.start - 1, interval.end + 1) for
                            interval in merged_intervals]
        self._extract_parts(merged_intervals)
        self._merge_parts()
        print("Output file: {}".format(self._out_path))

    def _get_selected_nums(self) -> Set[int]:
        with self._txt_path.open("r", encoding="utf-8") as s:
            nums = []
            for line in s:
                num, *_ = line.split("/ ", maxsplit=1)
                nums.append(num)
        nums = set(nums)
        return nums

    def _get_selected_intervals(self, nums: Set[int]) -> List[Interval]:
        with self._time_path.open("r", encoding="utf-8") as s:
            interval_by_num = {}
            for line in s:
                num, start, end = line.strip().split("/", maxsplit=2)
                if num in nums:
                    interval_by_num[num] = Interval(float(start), float(end))
        return sorted(interval_by_num.values(), key=lambda i: i.start)

    def _merge_intervals(self, intervals):
        merged_intervals = []
        s = intervals[0].start
        e = intervals[0].end
        for i in range(1, len(intervals)):
            if e > intervals[i].start - 5.0:
                e = intervals[i].end
            else:
                merged_intervals.append(Interval(s, e))
                s = intervals[i].start
                e = intervals[i].end
        merged_intervals.append(Interval(s, intervals[len(intervals) - 1].end))
        return merged_intervals

    def _extract_parts(self, merged_intervals):
        with self._list_path.open("w", encoding="utf-8") as d:
            for i, interval in enumerate(merged_intervals):
                part_path = self._get_video_part_path(i)
                self._execute([
                    "ffmpeg", "-y", "-i", str(self._video_path), "-c", "copy",
                    "-ss", format_time(interval.start), "-to",
                    format_time(interval.end), str(part_path)
                ])

                d.write(f"file '{part_path.resolve()}'\n")

    def _execute(self, args):
        ret = subprocess.run(args, stdout=subprocess.PIPE)
        if ret.returncode != 0:
            print(ret.stderr, file=sys.stderr)
            raise Exception()
        return ret

    def _get_video_part_path(self, i):
        return self._video_path.parent / (
                self._video_path.stem + f"-part{i}" + self._video_path.suffix)

    def _merge_parts(self):
        self._execute([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
            str(self._list_path),
            "-c", "copy", str(self._out_path)
        ])


def main():
    parser = argparse.ArgumentParser(
        description='VideoCutter: extract text/assemble video.')
    subparsers = parser.add_subparsers(dest='cmd', help='extract/assemble')
    extract_parser = subparsers.add_parser('e', help='extract the text')
    extract_parser.add_argument('-m', '--model', default='models/fr',
                                help='the model')
    extract_parser.add_argument('video_file', type=Path)

    assemble_parser = subparsers.add_parser('a', help='assemble the video')
    assemble_parser.add_argument('video_file', type=Path)
    args = parser.parse_args()

    if args.cmd == 'e':
        VideoCutter(args.video_file).extract_text(args.model)
    elif args.cmd == 'a':
        VideoCutter(args.video_file).assemble()


if __name__ == '__main__':
    main()
