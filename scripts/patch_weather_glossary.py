#!/usr/bin/env python3
from pathlib import Path
import json
path=Path('data/glossary.json')
try: glossary=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'version':'5.3','sections':[]}
except Exception: glossary={'version':'5.3','sections':[]}
sections=[s for s in glossary.setdefault('sections',[]) if s.get('title')!='Weather / Park Terms']
sections.append({'title':'Weather / Park Terms','items':[
{'term':'Wind Out','meaning':'Wind blowing from home plate toward the outfield. Usually helps fly balls carry farther.'},
{'term':'Wind In','meaning':'Wind blowing from the outfield toward home plate. Usually suppresses fly-ball distance.'},
{'term':'Crosswind','meaning':'Wind blowing across the field, such as left-to-right or right-to-left. It can help or hurt depending on spray direction.'},
{'term':'Carry','meaning':'How much the weather environment helps or hurts fly-ball distance.'},
{'term':'Temperature','meaning':'Warmer air is less dense and can help the ball travel farther. Cold air usually suppresses carry.'},
{'term':'Humidity','meaning':'Moist air can be slightly less dense than dry air, but humidity also interacts with temperature and park conditions.'},
{'term':'Dew Point','meaning':'A measure of moisture in the air. Higher dew points can indicate heavier, more humid game conditions.'},
{'term':'Air Density','meaning':'How thick the air is. Lower air density generally helps baseballs travel farther.'},
{'term':'Roof Status','meaning':'Whether a stadium roof is open or closed. Closed roofs reduce or remove wind/weather impact.'},
{'term':'Park Factor','meaning':'How much a ballpark increases or decreases home runs compared with league average.'},
{'term':'HR Park Factor','meaning':'A park-specific measure focused on home run friendliness.'},
{'term':'Pull-Side Park Factor','meaning':'How favorable the park is to the hitter pull side.'},
{'term':'Wall Height','meaning':'Outfield fence height. Taller walls can turn would-be home runs into doubles or outs.'},
{'term':'Field Orientation','meaning':'The direction the ballpark faces. This affects how wind direction maps onto left, center, or right field.'}
]})
glossary['sections']=sections; glossary['version']='5.3'; path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(glossary,indent=2),encoding='utf-8')
print('Patched weather glossary terms')
