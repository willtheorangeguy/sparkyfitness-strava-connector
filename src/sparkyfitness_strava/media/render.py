"""Local, deterministic concept renderer. No browser session or network access."""
import argparse
import base64
from html import escape
from pathlib import Path
from .art import body
from .comparison_art import illustration
from .comparisons import REFERENCES, compare
from .summary import POUNDS_PER_KG, demo

FONT = Path(__file__).parent / 'assets/InterVariable.woff2'

CSS = '''
@font-face{font-family:Inter;src:url(data:font/woff2;base64,FONT_DATA) format('woff2');font-weight:100 900}
*{box-sizing:border-box}body{margin:0;font-family:Inter,sans-serif;font-feature-settings:'tnum';color:var(--ink)}
.card{position:relative;width:1080px;height:1080px;padding:64px;overflow:hidden;background:var(--bg);color:var(--ink)}
.light{--bg:#f4f5f8;--ink:#142b49;--muted:#6c7b8e;--accent:#266dd3;--line:#d9e1ec;--panel:#fff;--inactive:#dce3ec;--muscle:#c5d0df;--primary:#266dd3;--secondary:#a6c8f5;--body:#e8edf4;--animal:#5484c6;--ear:#3669ad}
.dark{--bg:#0c1729;--ink:#f5f8ff;--muted:#90a5c0;--accent:#6fa9ff;--line:#293a50;--panel:#142339;--inactive:#263950;--muscle:#39516d;--primary:#5a9ef5;--secondary:#a3cef7;--body:#1c2e44;--animal:#6394d6;--ear:#3c6aa7}
.dark:before{content:'';position:absolute;right:-240px;top:240px;width:720px;height:720px;border:1px solid #213752;border-radius:50%;pointer-events:none}
.brand{display:flex;align-items:center;gap:13px;font-weight:760;font-size:29px;letter-spacing:-1px}
.brand-mark{width:34px;height:28px;color:var(--accent)}.brand span{font-weight:450;color:var(--muted);margin-left:8px;font-size:17px;letter-spacing:0}
.top{display:flex;align-items:center;justify-content:space-between}.tag{font-size:13px;letter-spacing:2.2px;font-weight:650;color:var(--muted)}
.kicker{margin-top:59px;font-size:15px;letter-spacing:2px;font-weight:650;color:var(--accent)}
h1{font-size:75px;line-height:1.05;letter-spacing:-4px;margin:17px 0 0;font-weight:650;max-width:930px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.summary h1{white-space:nowrap;text-overflow:ellipsis;display:block;font-size:clamp(38px,7vw,75px)}
.sub{font-size:19px;color:var(--muted);margin-top:20px;line-height:1.5}
.summary .kicker{margin-top:42px}
.summary-main{display:grid;grid-template-columns:220px 1fr;gap:24px;margin-top:32px;height:660px}
.metric{border-bottom:1px solid var(--line);padding:26px 0}.metric:first-child{padding-top:2px}.metric:last-child{border:0}
.label{font-size:15px;color:var(--muted);margin-bottom:8px}.value{font-size:49px;font-weight:630;letter-spacing:-2px;line-height:1.12}.unit{font-size:22px;font-weight:450;letter-spacing:-.5px;color:var(--muted);margin-left:6px}
.pair{display:flex;gap:44px}.pair .value{font-size:43px}
.anatomy{position:relative;border-radius:25px;background:var(--panel);padding:27px 25px 20px;border:1px solid var(--line)}
.diagram-title{font-size:13px;letter-spacing:1.8px;font-weight:650;color:var(--muted)}
.bodies{display:flex;height:555px;justify-content:center;gap:30px;margin-top:15px}.figure{width:270px;text-align:center}.figure svg{height:510px;width:262px}.figure-label{font-size:11px;letter-spacing:2px;color:var(--muted);margin-top:3px}
.body-base{fill:var(--body);stroke:var(--muscle);stroke-width:.8}.muscle{stroke:var(--panel);stroke-width:.9;stroke-linejoin:round;fill:var(--inactive)}.muscle.primary{fill:var(--primary)}.muscle.secondary{fill:var(--secondary)}.body-detail{stroke:var(--muscle);stroke-width:1;fill:none}
.legend{display:flex;gap:23px;justify-content:center;font-size:11px;color:var(--muted)}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--primary);margin-right:7px}.dot.secondary{background:var(--secondary)}
.muscle-list{display:flex;align-items:center;gap:10px;margin-top:24px;font-size:14px;color:var(--muted)}.muscle-list strong{color:var(--ink);font-weight:550}
.comparison .kicker{margin-top:68px}.hero-number{font-size:153px;font-weight:650;letter-spacing:-9px;line-height:1;margin-top:18px}.hero-number .unit{font-size:52px;color:var(--ink);letter-spacing:-2px;margin-left:13px}
.comparison h1{font-size:49px;letter-spacing:-2px;line-height:1.2;margin-top:27px;max-width:950px;display:block;overflow:visible}.animal{position:absolute;top:540px;left:145px;width:790px;color:var(--accent)}
.animal-body{fill:var(--animal);stroke:var(--ink);stroke-opacity:.15;stroke-width:2}.animal-ear{fill:var(--ear)}.animal-back{fill:var(--ear)}.animal-line{fill:none;stroke:var(--ear);stroke-width:9;stroke-linecap:round}.animal-tusk{fill:#f2ede3}.animal-eye{fill:#142b49}
.comparison-note{position:absolute;top:970px;left:64px;right:64px;text-align:center;color:var(--muted);font-size:18px}.approx{font-size:11px;margin-top:13px;color:var(--muted)}
'''


def html(summary, theme, kind):
    if theme not in {'light', 'dark'} or kind not in {'summary', 'comparison'}:
        raise ValueError('Unknown design theme or card kind')
    e = lambda key: escape(str(summary[key]))
    header = '''<div class="top"><div class="brand"><svg class="brand-mark" viewBox="0 0 40 30"><path d="M3 9v12M9 4v22M15 15h10M31 4v22M37 9v12" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg>SparkyFitness<span>workout stories</span></div><div class="tag">STRENGTH / 01</div></div>'''
    if kind == 'summary':
        volume_size = min(49, 310 / max(6, len(str(summary['volume']))))
        figures = ''.join('<div class="figure">'+body(summary['primary'], summary['secondary'], back)+'<div class="figure-label">'+label+'</div></div>' for back, label in [(False,'FRONT'),(True,'BACK')])
        content = f'''<div class="kicker">{e('date')} · WORKOUT COMPLETE</div><h1>{e('title')}. Full effort.</h1>
        <div class="summary-main"><div>
          <div class="metric"><div class="label">Total volume</div><div class="value" style="font-size:{volume_size}px">{e('volume')}<span class="unit" style="font-size:{min(22, volume_size * .45)}px">{e('units')}</span></div></div>
          <div class="metric"><div class="label">Time well spent</div><div class="value">{e('duration')}</div></div>
          <div class="metric pair"><div><div class="label">Exercises</div><div class="value">{e('exercise_count')}</div></div><div><div class="label">Sets</div><div class="value">{e('set_count')}</div></div></div>
        </div><div class="anatomy"><div class="diagram-title">MUSCLES WORKED</div><div class="bodies">{figures}</div><div class="legend"><span><i class="dot"></i>Primary</span><span><i class="dot secondary"></i>Secondary</span><span>Not intensity</span></div></div></div>
        <div class="muscle-list"><strong>THE FOCUS</strong> &nbsp; {escape(' · '.join(str(m).replace('_',' ').title() for m in summary['primary']))} <span style="margin-left:auto;font-size:11px">Schematic anatomy</span></div>'''
    else:
        display_mass = summary['volume_kg'] * (POUNDS_PER_KG if summary['units'] == 'lb' else 1)
        comparison = compare(display_mass, summary['units'])
        number_size = min(153, 1400 / (len(str(summary['volume'])) + 2))
        content = f'''<div class="kicker">YOU LIFTED</div><div class="hero-number" style="font-size:{number_size}px">{e('volume')}<span class="unit">{e('units')}</span></div>
        <h1>{escape(comparison['name'])}</h1><div class="sub">{escape(comparison['equivalent'])}</div>
        <div class="animal">{illustration(comparison['object'], comparison['name'])}</div><div class="comparison-note">{escape(comparison['reference'])}<div class="approx">Illustrative estimate · external load × repetitions</div></div>'''
    css = CSS.replace('FONT_DATA', base64.b64encode(FONT.read_bytes()).decode())
    return '<!doctype html><html><head><meta charset="utf-8"><style>'+css+'</style></head><body><main class="card '+theme+' '+kind+'">'+header+content+'</main></body></html>'


def render(output):
    from playwright.sync_api import sync_playwright
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chromium')
        context = browser.new_context(viewport={'width':1080,'height':1080}, device_scale_factor=1)
        context.route('**/*', lambda route: route.abort())
        page = context.new_page()
        for theme in ('light', 'dark'):
            for kind in ('summary', 'comparison'):
                content = html(demo(), theme, kind)
                page.set_content(content)
                page.evaluate('document.fonts.ready')
                page.screenshot(path=str(output/f'{theme}-{kind}.png'))
                (output/f'{theme}-{kind}.html').write_text(content, encoding='utf-8')
        previews = []
        for theme, title in [('dark','MIDNIGHT BLUE / SELECTED DESIGN')]:
            images = ''.join('<img src="data:image/png;base64,'+base64.b64encode((output/f'{theme}-{kind}.png').read_bytes()).decode()+'">' for kind in ('summary','comparison'))
            previews.append('<h2>'+title+'</h2><div class="row">'+images+'</div>')
        contact = '<!doctype html><meta charset="utf-8"><style>'+css_font()+'''body{margin:0;padding:50px 64px;background:#e9edf3;color:#142b49;font-family:Inter,sans-serif}h1{font-size:32px;letter-spacing:-1px;margin:0}p{font-size:16px;color:#697b92;margin:12px 0 30px}h2{font-size:13px;letter-spacing:2px;margin:27px 0 16px}.row{display:flex;gap:32px}.row img{width:600px;height:600px;border-radius:8px;box-shadow:0 3px 12px #142b4910}</style><h1>Your workout, in midnight blue.</h1><p>Larger muscle diagrams. No footer tagline. Weight comparisons that follow your total.</p>'''+''.join(previews)
        page.set_viewport_size({'width':1360,'height':830})
        page.set_content(contact)
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(output/'concepts.png'), full_page=True)
        gallery = ''.join('<div class="tile">'+illustration(item.key, item.name)+'<h2>'+escape(item.name)+'</h2><p>'+f'{item.kg:,} kg'+'</p></div>' for item in REFERENCES)
        page.set_content('<!doctype html><style>'+CSS.replace('FONT_DATA', base64.b64encode(FONT.read_bytes()).decode())+'''body{background:#0c1729;color:#f5f8ff;padding:40px}body:before{display:none}h1{font-size:32px;letter-spacing:-1px;margin:0 0 30px}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:18px}.tile{padding:14px;background:#142339;border-radius:16px}.tile svg{width:100%;height:130px}.tile h2{font-size:14px;line-height:1.3;margin:8px 0}.tile p{font-size:12px;color:#90a5c0}</style><body class="dark"><h1>30 ways to put your workout in perspective.</h1><div class="grid">'''+gallery+'</div></body>')
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(output/'comparison-catalog.png'), full_page=True)
        browser.close()


def css_font():
    return "@font-face{font-family:Inter;src:url(data:font/woff2;base64,"+base64.b64encode(FONT.read_bytes()).decode()+") format('woff2');font-weight:100 900}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('/previews'))
    render(parser.parse_args().output)
