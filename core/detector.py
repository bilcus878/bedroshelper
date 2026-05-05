import re
from dataclasses import dataclass


@dataclass
class Sector:
    sector_id: int
    href: str               # "?page=0&id_sektor=47"
    title: str              # "Sektor 47"
    centroid: tuple[int, int]   # pixel coords relative to the map image


async def detect_colonizable_sectors(page) -> list[Sector]:
    """
    Read <area> elements from the game's image map.
    Colonizable sectors have alt="Sektor <number>".
    Occupied/race sectors have alt="Sektor <RaceName>" — these are skipped.
    """
    areas = await page.evaluate("""() => {
        const map = document.querySelector('map[name="mapa_vesmiru"]') ||
                    document.querySelector('#mapa_vesmiru');
        if (!map) return [];
        return Array.from(map.querySelectorAll('area')).map(a => ({
            href: a.getAttribute('href') || '',
            alt:  a.getAttribute('alt')  || '',
            coords: a.getAttribute('coords') || '',
        }));
    }""")

    sectors = []
    for area in areas:
        m = re.match(r'^Sektor\s+(\d+)$', area['alt'].strip())
        if not m:
            continue

        sector_id = int(m.group(1))
        raw = [int(x.strip()) for x in area['coords'].split(',') if x.strip().lstrip('-').isdigit()]
        points = [(raw[i], raw[i + 1]) for i in range(0, len(raw) - 1, 2)]
        if not points:
            continue

        cx = int(sum(p[0] for p in points) / len(points))
        cy = int(sum(p[1] for p in points) / len(points))

        sectors.append(Sector(
            sector_id=sector_id,
            href=area['href'],
            title=area['alt'].strip(),
            centroid=(cx, cy),
        ))

    return sectors
