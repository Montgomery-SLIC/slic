"""
Server-side EAF (ELAN Annotation Format) parser.

The primary parsing path is client-side JavaScript (load_transcript() in click_task.js).
This module provides an equivalent server-side parser for testing and future use.

Matches the JS behaviour exactly:
- Prefers TIER[1] (second tier) over TIER[0]
- TIME_VALUE is in milliseconds
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class Annotation:
    start_ms: int
    end_ms: int
    text: str


def parse_eaf(xml_content: str) -> list[Annotation]:
    """
    Parse ELAN EAF XML string.
    Returns list of Annotation(start_ms, end_ms, text) sorted by start_ms.
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f'Invalid EAF XML: {e}') from e

    # Build TIME_SLOT_ID → TIME_VALUE (ms) map
    time_order = root.find('TIME_ORDER')
    if time_order is None:
        return []

    slots: dict[str, int] = {}
    for slot in time_order.findall('TIME_SLOT'):
        slot_id = slot.get('TIME_SLOT_ID')
        time_val = slot.get('TIME_VALUE')
        if slot_id and time_val is not None:
            try:
                slots[slot_id] = int(time_val)
            except ValueError:
                pass

    # Select tier: prefer index 1 over index 0 (matches JS behaviour)
    tiers = root.findall('TIER')
    if not tiers:
        return []
    tier = tiers[1] if len(tiers) > 1 else tiers[0]

    annotations = []
    for annotation in tier.findall('ANNOTATION'):
        alignable = annotation.find('ALIGNABLE_ANNOTATION')
        if alignable is None:
            continue
        ref1 = alignable.get('TIME_SLOT_REF1')
        ref2 = alignable.get('TIME_SLOT_REF2')
        value_el = alignable.find('ANNOTATION_VALUE')
        if ref1 is None or ref2 is None or value_el is None:
            continue
        start = slots.get(ref1)
        end = slots.get(ref2)
        if start is None or end is None:
            continue
        text = (value_el.text or '').strip()
        annotations.append(Annotation(start_ms=start, end_ms=end, text=text))

    annotations.sort(key=lambda a: a.start_ms)
    return annotations
