"""Manual, optional: executable Chrome/Edge browser export test (Playwright)."""
from pathlib import Path
from shutil import which
from playwright.sync_api import sync_playwright
from PIL import Image
from xml.etree import ElementTree as ET
base=Path(__file__).resolve().parent.parent
url=(base/'examples/zju/workbench.html').resolve().as_uri()
out=base/'dist/browser-qa';out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=which('chromium') or which('google-chrome') or None,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    context=browser.new_context(accept_downloads=True,viewport={'width':1680,'height':960},device_scale_factor=1)
    page=context.new_page()
    errs=[]
    page.on('pageerror',lambda e:errs.append(str(e)))
    page.set_content((base/'examples/zju/workbench.html').read_text(encoding='utf-8'),wait_until='domcontentloaded',timeout=45000)
    page.locator('#previewCanvas').wait_for(timeout=45000)
    page.wait_for_timeout(1250)
    print('default color:',page.locator('#hex').input_value(),'intensity:',page.locator('#intensity').input_value(),'detail:',page.locator('#detail').input_value())
    page.screenshot(path=str(out/'editor-browser-preview.png'),full_page=True)
    with page.expect_download(timeout=120000) as info:
        page.locator('#svgTransparent').click()
    d=info.value;target=out/'exported-transparent.svg';d.save_as(target)
    txt=target.read_text('utf-8');root=ET.fromstring(txt)
    assert not root.findall('.//{http://www.w3.org/2000/svg}image')
    print('svg bytes:',target.stat().st_size,'paths:',len(root.findall('.//{http://www.w3.org/2000/svg}path')))
    with page.expect_download(timeout=120000) as info2:
        page.locator('#pngTransparent').click()
    d2=info2.value;target2=out/'exported-transparent.png';d2.save_as(target2)
    im=Image.open(target2)
    print('PNG:',im.size,im.mode,'top-left-alpha:',im.getpixel((300,50))[3])
    assert im.size==(3840,2160) and im.getpixel((300,50))[3]==0
    assert not errs,errs
    browser.close()
print('BROWSER SMOKE PASS')
