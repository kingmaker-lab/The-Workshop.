"""Teste visual do terminal com Playwright (a navegação real é bloqueada por política do Chromium deste ambiente)."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'index.html').read_text()
CSS=(ROOT/'assets/styles.css').read_text()+'\n'+(ROOT/'assets/vulpes.css').read_text()
JS=(ROOT/'js/vulpes-data.js').read_text().replace('export const DATA','const DATA')+'\n'+(ROOT/'js/vulpes-engine.js').read_text().replace("import { DATA } from './vulpes-data.js';",'').replace('export const ', 'const ').replace('export function ', 'function ').replace('export class ', 'class ')+'\n'+(ROOT/'js/vulpes77.js').read_text().replace("import { VulpesGame } from './vulpes-engine.js';",'').replace("import { DATA } from './vulpes-data.js';",'')
KEY='wolfpack-workshop-vulpes77-web-v01'
def load(page, save=None):
    page.set_content(HTML, wait_until='domcontentloaded')
    # about:blank não permite localStorage. Simulamos a API apenas para testar a UI.
    page.evaluate("""(saved) => { const map={}; if(saved) map['wolfpack-workshop-vulpes77-web-v01']=saved;
       Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem(k){return map[k]??null},setItem(k,v){map[k]=v},removeItem(k){delete map[k]}}}); }""",save)
    page.add_style_tag(content=CSS)
    page.add_script_tag(content=JS)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    load(page)
    assert page.locator('#v77-stage').inner_text()=='01 / 03'
    assert 'O ECO FANTASMA' in page.locator('#v77-mission-title').inner_text()
    assert '10.77.0.12' in page.locator('#v77-nodes').inner_text()
    page.screenshot(path=str(ROOT/'preview-desktop.png'),full_page=True)
    page.locator('#vulpes').scroll_into_view_if_needed()
    page.screenshot(path=str(ROOT/'preview-vulpes.png'))
    page.locator('#vulpes').screenshot(path=str(ROOT/'preview-vulpes-section.png'))
    cmds=['map','scan 10.77.0.12','connect 10.77.0.12:8080','cat traffic.log','decode b64 TklHSFRKQVI=','submit NIGHTJAR','scan 10.77.0.23','connect 10.77.0.23:9200','grep E-441 auth.log','submit svc-bridge','scan 10.77.0.44','connect 10.77.0.44:8443','cat incident.json','contain 10.77.0.12','submit IR-2607']
    for cmd in cmds:
        page.locator('#v77-input').fill(cmd)
        page.locator('#v77-form button[type=submit]').click()
        page.wait_for_function("document.querySelector('#v77-input').disabled === false")
    assert page.locator('#v77-score').inner_text()=='300 / 300 XP'
    assert 'CONCLUÍDA' in page.locator('#v77-mission-title').inner_text()
    assert page.locator('#v77-rank').inner_text()=='VULPES OPERATOR'
    saved=page.evaluate(f"localStorage.getItem('{KEY}')")
    assert saved and json.loads(saved)['score']==300
    resume=browser.new_page(viewport={'width':1440,'height':900})
    load(resume,saved)
    assert resume.locator('#v77-score').inner_text()=='300 / 300 XP'
    assert resume.locator('#v77-stage').inner_text()=='03 / 03 ✓'
    assert not errors,errors
    print(f'✓ UI desktop: {len(cmds)} comandos, campanha concluída, reidratação do save, sem erros de script.')
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
    load(mobile)
    mobile.screenshot(path=str(ROOT/'preview-mobile.png'),full_page=True)
    assert mobile.locator('#v77-stage').inner_text()=='01 / 03'
    mobile.locator('#v77-input').fill('status')
    mobile.locator('#v77-form button').click()
    mobile.wait_for_function("document.querySelector('#v77-input').disabled === false")
    assert 'Pontos acumulados: 0' in mobile.locator('#v77-output').inner_text()
    print('✓ UI mobile: interface carregada e terminal interativo.')
    browser.close()
