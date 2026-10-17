"""Run directly: .venv/bin/python tests/test_product_recommender.py."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tools.product_recommender import recommend_products, TOOL_SPEC


def main():
    clinical = recommend_products('agilent', 'measure mitochondrial respiration in PBMCs for a diabetes trial')
    assert clinical[0]['id'] == 'seahorse-xf'
    assert recommend_products('agilent', '', {'regulatory': 'IVD'})[0]['id'] == 'nanozoomer-ivd'
    assert recommend_products('cisco', 'router', {'deployment': 'cloud'})[0]['id'] == 'catalyst-8000v'
    branch = recommend_products('cisco', 'branch SD-WAN redundant power', {'needs_redundancy': True}, 50)
    entries = {r['id']: r for r in json.loads(Path('app/catalog/cisco_routers.json').read_text())}
    assert entries[branch[0]['id']]['power_supply_redundancy'] is True
    assert all(branch[i]['final_score'] >= branch[i+1]['final_score'] for i in range(len(branch)-1))
    for row in branch:
        assert math.isclose(row['final_score'], row['similarity'] + row['context_adjustment'])
        assert math.isfinite(row['final_score']) and row['source_url'].startswith('https://')
    capacity = recommend_products('cisco', '', {'throughput_gbps': 10}, 50)
    by_id = {r['id']: r for r in capacity}
    assert by_id['c8300-2n2s-4t2x']['context_adjustment'] == 0.2
    assert by_id['c8200-1n-4t']['context_adjustment'] == -0.3
    cheap = recommend_products('cisco', '', {'budget': 'low'})
    assert all(entries[r['id']]['family'] == 'Catalyst 8200' or r['model'] in {'ISR4221', 'ISR4221X', 'ISR4321'} for r in cheap)
    assert branch == recommend_products('cisco', 'branch SD-WAN redundant power', {'needs_redundancy': True}, 50)
    unknown = recommend_products('agilent', 'zzzxxyy')
    assert all(r['similarity'] == 0 and r['matched_terms'] == [] for r in unknown)
    assert recommend_products('cisco', '', k=0) == []
    for args in [('invalid', ''), ('cisco', '', {'throughput_gbps': float('nan')}), ('agilent', '', {'unknown': 1}), ('cisco', '', None, -1)]:
        try:
            recommend_products(*args)
        except ValueError:
            pass
        else:
            raise AssertionError('Expected ValueError')
    assert TOOL_SPEC['function']['name'] == 'recommend_products'
    print('PASS: clinical relevance, IVD, cloud, redundancy, ranking, score accounting, empty/OOV queries, validation and tool schema')


if __name__ == '__main__':
    main()
