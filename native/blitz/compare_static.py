#!/usr/bin/env python3
"""Produce an annotated, size-aligned screenshot comparison (NOT CSS parity)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat, ImageOps, ImageDraw


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(reference: Path, candidate: Path, output: Path, *, threshold: int = 32) -> dict:
    if not 0 < threshold < 256:
        raise ValueError('Threshold must be an integer between 1 and 255')
    with Image.open(reference) as p, Image.open(candidate) as q:
        ref = p.convert('RGB')
        test = q.convert('RGB')
        if ref.size != test.size:
            raise ValueError(f'Incomparable viewport geometry: reference={ref.size}, candidate={test.size}')
        if ref.size[0] < 240 or ref.size[1] < 240:
            raise ValueError('Reference screenshot too small for a useful comparison')
        delta = ImageChops.difference(ref, test)
        abs_mean = sum(ImageStat.Stat(delta).mean) / 3.0
        # A pixel is considered changed if ANY channel differs by threshold.
        changed = sum(max(pixel) >= threshold for pixel in delta.get_flattened_data())
        total = ref.width * ref.height
        # Contrast-enhanced difference image, deliberately not SSIM or CSS compatibility.
        diff = delta.point(lambda x: min(x * 3, 255))
        label_height = 40
        image = Image.new('RGB', (ref.width * 3, ref.height + label_height), '#111721')
        for i, (pic, label) in enumerate(((ref, 'Chromium static baseline'),
                                          (test, 'Blitz Vello CPU'),
                                          (diff, 'Absolute pixel difference (3x contrast)'))):
            ox = ref.width * i
            image.paste(pic, (ox, label_height))
            ImageDraw.Draw(image).text((ox + 20, 13), label, fill='#f0f4f4')
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
    result = {
        'schema': 'calyra.visual-comparison.v1',
        'reference_sha256': sha(reference),
        'candidate_sha256': sha(candidate),
        'size': list(ref.size),
        'rgb_mean_absolute_difference_0_to_255': round(abs_mean, 4),
        'changed_pixel_fraction_threshold_32': round(changed / total, 6),
        'threshold': threshold,
        'composite_image': str(output),
        'not_a_css_compatibility_score': True,
        'caveat': 'Font rasterization, anti-aliasing, layout, color management and unimplemented effects all influence the result; pixel statistics alone cannot identify which CSS properties failed.',
    }
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.reference, args.candidate, args.output), indent=2))
