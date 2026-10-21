"""Local SVG illustrations for the reference-weight catalog.

The carrier adapts a credited CC BY-SA silhouette; other artwork is original.
"""
from html import escape

from .art import elephant


def wheels(*centers, radius=30):
    return ''.join(f'<circle cx="{x}" cy="285" r="{radius}" fill="var(--ear)"/>'
                   f'<circle cx="{x}" cy="285" r="{radius // 2}" fill="var(--muted)"/>' for x in centers)


def windows(xs, y=160, width=40, height=45):
    return ''.join(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="5" fill="var(--panel)"/>' for x in xs)


def whale(kind):
    """Species-specific profiles; pale markings use the shared illustration palette."""
    return SEA_ANIMALS[kind]


SEA_ANIMALS = {
    'orca': '''
        <path d="M285 205Q265 259 312 287L335 217Z" fill="var(--ear)"/>
        <path d="M105 205Q116 168 176 145Q235 121 324 138
                 Q344 109 360 46Q379 51 390 145Q475 162 556 209
                 Q590 197 622 167L649 161Q637 190 612 219
                 Q651 227 672 256Q619 259 575 236
                 Q461 266 304 265Q175 268 122 236Q101 224 105 205Z"/>
        <path d="M112 221Q177 246 253 226Q298 215 340 233
                 Q409 254 501 237Q422 276 287 259Q169 262 122 236Z" fill="#dcecff"/>
        <path d="M206 174Q231 154 260 165Q273 177 248 188Q218 197 206 184Z" fill="#dcecff"/>
        <path d="M385 160Q410 148 440 170L414 184Z" fill="var(--muted)"/>
        <path d="M288 220Q310 273 376 294Q365 253 335 226Z" fill="var(--ear)"/>
        <path d="M112 218Q144 226 179 219" fill="none" stroke="var(--ear)" stroke-width="4"/>
        <circle cx="178" cy="190" r="5" fill="var(--panel)"/>
    ''',
    'whale_shark': '''
        <path d="M272 209L329 292Q345 298 342 280L323 215M435 214L478 259 476 218Z" fill="var(--ear)"/>
        <path d="M91 182Q128 141 241 147L342 151Q373 111 388 87
                 Q405 109 418 160L515 185 573 201Q600 173 633 112
                 L650 102Q647 167 614 211Q639 243 641 283
                 Q606 263 577 229Q510 235 433 247L237 258
                 Q141 258 97 224Q83 211 91 182Z"/>
        <path d="M96 221Q202 252 361 235L566 217Q439 257 237 258Q141 258 97 224Z" fill="#dcecff"/>
    ''' + ''.join(
        f'<circle cx="{x}" cy="{y}" r="3.5" fill="#dcecff"/>'
        for x in range(281, 506, 24)
        for y in (166 + max(0, x - 340) // 4 + offset for offset in (0, 14, 28))
        if y <= 230
    ) + '''
        <path d="M294 202Q331 234 397 266Q403 270 397 258L340 192Z" fill="var(--ear)"/>
        <path d="M100 199Q138 185 178 197M209 181L214 220M224 179L231 222M240 179L247 222M256 180L263 221" fill="none" stroke="var(--ear)" stroke-width="4"/>
        <path d="M310 169L540 204M416 220L538 215" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <circle cx="173" cy="180" r="5" fill="var(--panel)"/>
    ''',
    'humpback': '''
        <path d="M108 198Q126 164 194 149Q269 119 352 152
                 Q418 165 449 155L471 137 486 171Q535 191 576 197
                 Q595 172 647 158L676 163Q645 192 612 211
                 Q650 217 671 241Q622 247 579 225
                 Q477 263 332 266Q178 280 119 234Q101 219 108 198Z"/>
        <path d="M111 220Q203 246 300 229L391 244Q280 285 180 255Q133 242 111 220Z" fill="#dcecff"/>
        <path d="M148 231Q188 250 236 255M169 226Q213 246 262 253M197 225Q244 242 285 246" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <path d="M281 215Q297 249 362 284L423 310Q444 318 449 307
                 L429 291 395 267 354 226 320 207Z" fill="var(--ear)"/>
        <path d="M303 229Q343 274 427 307" fill="none" stroke="#dcecff" stroke-width="6"/>
        <path d="M112 210Q159 226 235 207" fill="none" stroke="var(--ear)" stroke-width="4"/>
        <circle cx="186" cy="186" r="5" fill="var(--panel)"/>
        <g fill="var(--ear)"><circle cx="125" cy="183" r="5"/><circle cx="145" cy="171" r="5"/><circle cx="168" cy="161" r="5"/><circle cx="190" cy="154" r="4"/></g>
    ''',
    'blue_whale': '''
        <path d="M80 195Q89 171 153 157Q261 132 394 160
                 L507 183Q521 164 536 161L544 191 599 204
                 Q621 177 664 164L690 167Q675 194 643 215
                 Q675 224 690 246Q646 247 607 230
                 Q502 252 348 257Q177 266 102 233Q77 223 80 195Z"/>
        <path d="M84 215Q199 249 374 236L581 221Q465 255 318 257Q153 261 102 233Z" fill="#dcecff"/>
        <path d="M97 209Q185 231 282 213M122 227Q203 250 294 244M148 225Q231 246 322 241M177 222Q257 240 340 236" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <path d="M298 219Q332 256 405 277Q421 278 412 268L345 214Z" fill="var(--ear)"/>
        <path d="M237 176Q326 161 413 186M405 205L465 209" fill="none" stroke="var(--ear)" stroke-width="5" opacity=".4"/>
        <circle cx="193" cy="196" r="4.5" fill="var(--panel)"/>
    ''',
}


def illustration(key, label=''):
    if key == 'elephant':
        return elephant().replace('Original elephant illustration', escape(label or 'African elephant', quote=True)+' illustration')
    if key in {'orca', 'whale_shark', 'humpback', 'blue_whale'}:
        shapes = whale(key)
    else:
        shapes = SHAPES[key] if key is not None else '<path d="M260 165V245M285 140V270M310 205H450M475 140V270M500 165V245" fill="none" stroke="var(--animal)" stroke-width="20" stroke-linecap="round"/>'
    return ('<svg viewBox="0 0 760 370" role="img" aria-label="'+escape(label, quote=True)+' illustration">'
            '<ellipse cx="380" cy="337" rx="275" ry="11" fill="currentColor" opacity=".07"/>'
            '<g fill="var(--animal)" stroke-linejoin="round" stroke-linecap="round">'+shapes+'</g></svg>')


SHAPES = {
    'hippo': '''
        <path d="M219 238L211 307Q221 322 253 316L270 258M407 244L415 311Q431 324 454 313L461 244" fill="var(--ear)"/>
        <path d="M176 187Q148 202 141 235L128 245" fill="none" stroke="var(--ear)" stroke-width="9"/>
        <path d="M167 213Q154 156 212 119Q270 80 373 105Q449 109 483 154
                 Q514 137 547 158L578 185Q621 185 631 215L632 248Q622 273 571 279
                 L499 270 485 310Q474 332 442 321L434 267Q364 292 283 271
                 L274 315Q255 331 227 320L231 265Q180 258 167 213Z"/>
        <path d="M476 163Q455 136 467 124Q486 118 497 146M537 158Q533 132 550 132Q566 142 555 166"/>
        <path d="M486 178Q460 207 487 246M505 252Q557 265 611 248" fill="none" stroke="var(--ear)" stroke-width="5"/>
        <path d="M510 256L514 268 524 258" fill="#dcecff"/>
        <ellipse cx="590" cy="209" rx="8" ry="5" fill="var(--ear)"/>
        <ellipse cx="615" cy="216" rx="5" ry="4" fill="var(--ear)"/>
        <circle cx="537" cy="183" r="5" fill="var(--panel)"/>
        <path d="M239 316V309M251 319V311M452 319V311M464 318V310" stroke="var(--ear)" stroke-width="3"/>
    ''',
    'container': '<path d="M133 125L574 93 627 125V295L185 315 133 286Z"/><path d="M185 148L627 125M185 148V315" fill="none" stroke="var(--ear)" stroke-width="8"/>'+''.join(f'<path d="M{x} 153V293" stroke="var(--ear)" stroke-width="6"/>' for x in range(215,610,33)),
    'pickup': '''
        <path d="M117 196H319L358 134Q363 126 376 126H465Q480 126 488 139L537 193
                 L608 201Q624 205 630 223L641 271H595Q590 232 551 232Q512 232 507 271
                 H271Q266 232 227 232Q188 232 183 271H117Z"/>
        <path d="M335 190L371 141H402V190Z M413 141H463L504 190H413Z" fill="var(--panel)"/>
        <path d="M124 207H308V250M321 199V259M411 199V259M516 202V226" fill="none" stroke="var(--ear)" stroke-width="4"/>
        <path d="M126 190H308M280 271H494" stroke="var(--ear)" stroke-width="9"/>
        <path d="M424 207H442M548 212H594" stroke="var(--ear)" stroke-width="4"/>
        <path d="M608 214H626L631 231H608Z M119 211H132V231H119Z" fill="#dcecff"/>
        <path d="M111 263H177M600 263H648" stroke="var(--muted)" stroke-width="10"/>
        <path d="M502 185H521V199H502Z" fill="var(--ear)"/>
''' + wheels(227, 551, radius=36) + '''    ''',
    'forklift': '''
        <path d="M441 104H458V292H603V304H440Z" fill="var(--ear)"/>
        <path d="M420 107H433V280H420Z M428 245H461V257H428Z"/>
        <path d="M190 272V230Q190 212 211 212H271L295 244H358V216H408V280H190Z"/>
        <path d="M265 211V114H393V215M253 111H405" fill="none" stroke="var(--ear)" stroke-width="11"/>
        <path d="M279 126H377V201H279Z" fill="var(--panel)" opacity=".6"/>
        <path d="M301 181V219H333M331 238L355 195M345 190L367 202" fill="none" stroke="var(--ear)" stroke-width="9"/>
        <path d="M203 229H250M203 242H250" stroke="var(--ear)" stroke-width="4"/>
        <rect x="218" y="189" width="29" height="21" rx="7" fill="var(--ear)"/>
''' + wheels(226, radius=28) + wheels(382, radius=37) + '''    ''',
    'tractor': '''
        <path d="M316 248H597V274H316Z" fill="var(--ear)"/>
        <path d="M161 270V219L211 200 229 149H275V112Q275 99 289 99H373L398 130V258
                 H286Q274 235 249 235Q212 235 207 270Z"/>
        <path d="M242 159H274V198H227Z M288 131H352V192H288Z" fill="var(--panel)"/>
        <path d="M359 132L382 145V193H359Z" fill="var(--ear)"/>
        <path d="M282 205V248M354 202V249M298 207H315M170 226H204" stroke="var(--ear)" stroke-width="4"/>
        <path d="M164 237H192V261H164Z" fill="var(--ear)"/>
        <path d="M157 268H204M287 270H383" stroke="var(--muted)" stroke-width="10"/>
        <rect x="312" y="258" width="85" height="22" rx="8" fill="var(--muted)"/>
        <path d="M410 228V117H423M281 136H220V153" fill="none" stroke="var(--ear)" stroke-width="7"/>
        <path d="M476 241H550" stroke="var(--muted)" stroke-width="9"/>
        <path d="M437 264Q451 239 481 252Q517 237 550 251Q572 248 585 267" fill="none" stroke="var(--animal)" stroke-width="9"/>
    ''' + wheels(248, 465, 548, radius=35),
    'bus': '<rect x="112" y="126" width="540" height="153" rx="26"/>'+windows(range(144,603,60))+ '<path d="M118 233H642" stroke="var(--ear)" stroke-width="8"/>'+wheels(214,554),
    'bell': '<path d="M344 83Q344 48 380 48Q416 48 416 83L405 103H355Z" fill="var(--ear)"/><path d="M306 124Q312 91 380 91Q448 91 454 124L483 254 528 281Q540 303 507 305H253Q220 303 232 281L277 254Z"/><path d="M251 280H510M300 140H460" stroke="var(--ear)" stroke-width="9"/><circle cx="380" cy="310" r="21" fill="var(--ear)"/>',
    'excavator': '''
        <rect x="149" y="271" width="316" height="57" rx="28" fill="var(--ear)"/>
        <rect x="165" y="282" width="284" height="34" rx="17" fill="var(--muted)"/>
        <path d="M193 272V223Q193 206 211 206H290V153Q290 143 302 143H366L386 177V254H408V272Z"/>
        <path d="M304 157H354L371 181V219H304Z" fill="var(--panel)"/>
        <path d="M336 158V217M212 221H269M212 235H269" stroke="var(--ear)" stroke-width="4"/>
        <path d="M376 223L435 100Q444 84 459 96L548 164 576 256" fill="none" stroke="var(--animal)" stroke-width="27"/>
        <path d="M393 198L438 118M468 113L530 163M545 185L560 241" stroke="var(--ear)" stroke-width="9"/>
        <path d="M396 190L422 139M477 119L516 151M548 194L557 226" stroke="var(--muted)" stroke-width="4"/>
        <path transform="translate(1152 0) scale(-1 1)" d="M547 252L589 238 624 282Q606 308 559 306L539 288Z" fill="var(--ear)"/>
        <g fill="var(--ear)"><circle cx="190" cy="299" r="11"/><circle cx="240" cy="299" r="11"/><circle cx="290" cy="299" r="11"/><circle cx="340" cy="299" r="11"/><circle cx="390" cy="299" r="11"/><circle cx="425" cy="299" r="11"/></g>
        <g fill="var(--muted)"><circle cx="381" cy="216" r="7"/><circle cx="449" cy="103" r="7"/><circle cx="547" cy="168" r="7"/></g>
    ''',
    'stonehenge': '''
        <g fill="var(--ear)">
          <path d="M147 167L187 160 192 301 143 308Z M555 158L595 167 608 306 559 302Z M280 146L315 141 318 288 277 288Z M420 142L454 149 462 288H422Z"/>
          <path d="M134 143L196 135 205 168 134 179Z M549 136L606 146 614 178 547 169Z M266 120L463 122 469 153 270 153Z"/>
        </g>
        <path d="M205 119L261 114 270 321 200 321 197 287Z M335 118L389 122 396 323 327 323Z
                 M436 111L492 116 502 321 430 321Z M551 123L588 128 599 320 546 320Z"/>
        <path d="M185 83L274 76 401 86 408 128 316 137 184 129Z M420 79L514 82 602 94 609 135 518 132 417 122Z"/>
        <path d="M244 132L253 307M371 140L379 309M477 133L486 306M573 144L583 307" fill="none" stroke="var(--ear)" stroke-width="9"/>
        <path d="M197 111L276 104 387 111M432 104L509 108 591 118" fill="none" stroke="var(--ear)" stroke-width="4"/>
        <path d="M283 302L309 289 325 305 321 323H277Z M511 310L533 299 547 324H505Z" fill="var(--ear)"/>
    ''',
    'semi': '''
        <rect x="76" y="121" width="388" height="137" rx="5"/>
        <path d="M85 130H454V243H85Z" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <path d="M98 138V236M126 138V236M154 138V236M182 138V236M210 138V236M238 138V236
                 M266 138V236M294 138V236M322 138V236M350 138V236M378 138V236M406 138V236M434 138V236"
              stroke="var(--ear)" stroke-width="2" opacity=".5"/>
        <path d="M84 251H456" stroke="#dcecff" stroke-width="3" stroke-dasharray="14 11"/>
        <path d="M92 264H575V276H92Z" fill="var(--ear)"/>
        <path d="M479 261V146Q479 133 493 133H532L550 159V190H582L611 216 657 228V271
                 H642Q636 244 612 244Q586 244 581 271H479Z"/>
        <path d="M493 154H527V188H493Z M557 201H577L598 220H557Z" fill="var(--panel)"/>
        <path d="M487 200H539V252M547 195V258M558 232H574" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <path d="M644 234H657V258H644Z M467 224V161H474" fill="var(--ear)" stroke="var(--ear)" stroke-width="5"/>
        <path d="M648 268H671M511 273H574" stroke="var(--muted)" stroke-width="7"/>
        <path d="M653 228H662V238H653Z" fill="#dcecff"/>
    ''' + wheels(129, 185, 460, 512, 612, radius=26),
    'subway': '<rect x="99" y="126" width="563" height="157" rx="24"/>'+windows([125,181,311,367,497,553],width=42)+'<path d="M244 151H288V277H244Z M430 151H474V277H430Z" fill="var(--ear)"/><path d="M96 309H665M110 325H650" stroke="var(--ear)" stroke-width="6"/>',
    'locomotive': '''
        <path d="M116 249V212L160 202V148L151 136H262L280 165H590L625 188V248Z"/>
        <path d="M172 150H206V186H172Z M216 150H251L265 175V186H216Z" fill="var(--panel)"/>
        <path d="M288 175H582V231H288Z" fill="var(--ear)"/>
        <path d="M301 182V224M313 182V224M325 182V224M337 182V224M349 182V224M470 182V224M482 182V224M494 182V224M506 182V224M518 182V224M530 182V224M542 182V224M554 182V224" stroke="var(--animal)" stroke-width="4"/>
        <path d="M368 181H451V230H368Z"/>
        <path d="M387 190V220M431 190V220" stroke="var(--ear)" stroke-width="3"/>
        <path d="M324 164V152H363V164M482 164V151H521V164" fill="var(--ear)"/>
        <path d="M102 249H640V265H102Z M111 262L92 292H135L151 263Z" fill="var(--ear)"/>
        <path d="M126 241V213H151M282 239V210H614V240M335 211V239M409 211V239M482 211V239M555 211V239" fill="none" stroke="var(--muted)" stroke-width="4"/>
        <path d="M177 269H306M454 269H583" stroke="var(--ear)" stroke-width="16"/>
        <path d="M92 313H655M107 324H640" stroke="var(--ear)" stroke-width="4"/>
''' + wheels(185, 237, 289, 462, 514, 566, radius=22) + '''    ''',
    'liberty': '''
        <path d="M322 330V307H338V282H423V307H439V330Z" fill="var(--ear)"/>
        <path d="M342 283L353 199 348 151 323 128 295 74 308 67 343 113 365 127
                 L394 128 416 158 433 184 420 219 406 208 416 283Z"/>
        <path d="M365 127L360 111 363 95 389 95 396 112 389 132Z"/>
        <path d="M361 100L343 91 359 89 349 71 368 83 368 61 378 80 388 60 389 84 407 71 399 91 417 90 394 103Z" fill="var(--ear)"/>
        <path d="M370 107L382 110M377 119H385" stroke="var(--ear)" stroke-width="3"/>
        <path d="M298 78L291 53H311L307 78Z M287 51H314V57H287Z" fill="var(--ear)"/>
        <path d="M295 49Q279 36 298 17Q298 30 307 31Q321 45 305 49Z"/>
        <path d="M399 166L421 157 439 196 414 208Z" fill="var(--ear)"/>
        <path d="M404 171L418 166 430 193 417 199Z" fill="var(--muted)"/>
        <path d="M363 143L389 158 361 196M396 145L376 180 399 215M369 195L357 272M381 203L377 274M397 222L404 274M327 123L345 121" fill="none" stroke="var(--ear)" stroke-width="4"/>
        <path d="M346 299H416M333 317H427" stroke="var(--muted)" stroke-width="4"/>
    ''',
    'iss': '<g transform="rotate(-16 380 190)"><rect x="293" y="167" width="173" height="47" rx="18"/><path d="M380 116V270M162 191H600" stroke="var(--ear)" stroke-width="15"/>'+''.join(f'<rect x="{x}" y="{y}" width="92" height="100" rx="3" fill="var(--ear)" stroke="var(--accent)" stroke-width="3"/>' for x in (160,255,415,510) for y in (70,215))+'<path d="M286 190H474M380 141V237" stroke="var(--animal)" stroke-width="16"/></g>',
    # Side elevation: tail behind the fuselage, near wing and engines in front.
    'a380': '''
        <path d="M531 180L585 87H620L604 193Z" fill="var(--ear)"/>
        <path d="M95 207Q110 194 130 190L157 174Q170 167 197 167H531
                 Q571 168 600 184L660 206Q669 210 658 215L582 232
                 Q558 239 526 239H182Q133 239 103 224Q88 216 95 207Z"/>
        <path d="M129 189L158 177H184V191H129Z" fill="var(--panel)"/>
        <path d="M161 177V191" stroke="var(--animal)" stroke-width="4"/>
        <path d="M207 185H526M207 204H546" stroke="var(--panel)" stroke-width="5" stroke-dasharray="4 11"/>
        <path d="M190 180V222M285 180V222M487 180V222M549 193V220" stroke="var(--ear)" stroke-width="3"/>
        <path d="M111 220Q151 234 199 232H526Q552 232 578 226" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <path d="M334 214L393 215 507 265H462L354 237Z" fill="var(--ear)"/>
        <path d="M361 236L386 238 397 256H367Z M421 252L443 255 451 269H425Z" fill="var(--ear)"/>
        <path d="M354 249H399Q413 249 416 260L413 274H354Q344 261 354 249Z"/>
        <path d="M417 264H453Q465 265 467 275L463 285H417Q409 275 417 264Z"/>
        <ellipse cx="355" cy="261" rx="7" ry="12" fill="var(--ear)"/>
        <ellipse cx="418" cy="275" rx="5" ry="10" fill="var(--ear)"/>
        <path d="M553 211L616 234H650L595 208Z" fill="var(--ear)"/>
    ''',
    'mining_truck': '''
        <path d="M153 133L178 111 209 112 237 88 266 101 291 81 322 99 353 86 385 108 412 98 445 131Z" fill="var(--ear)"/>
        <path d="M128 127H452L478 174H565V192H443L413 230H188Z"/>
        <path d="M147 143H431L404 210H190Z" fill="var(--ear)"/>
        <path d="M201 148L218 204M268 148L279 204M335 148L337 204M402 148L389 204" stroke="var(--animal)" stroke-width="9"/>
        <path d="M190 239H444V195H554L593 229H622V278H180Z"/>
        <path d="M461 199H501V233H461Z M511 199H543L574 233H511Z" fill="var(--panel)"/>
        <path d="M451 186V166H554V184M469 166V183M532 166V183" fill="none" stroke="var(--ear)" stroke-width="5"/>
        <path d="M580 245H615V267H580Z M445 249H493V272H445Z" fill="var(--ear)"/>
        <path d="M462 246V312M480 246V312M462 264H480M462 280H480M462 296H480" stroke="var(--muted)" stroke-width="4"/>
''' + wheels(252, 535, radius=49) + '''    ''',
    'saturn_v': '''
        <g transform="translate(380 0) scale(.65 1) translate(-380 0)">
        <path d="M376 18H384V45H376Z M370 45H390L386 57H374Z" fill="var(--ear)"/>
        <path d="M375 55L370 78M385 55L390 78M374 60L388 72M386 60L372 72" fill="none" stroke="var(--ear)" stroke-width="2.5"/>
        <path d="M380 72L393 91V110L405 136V307H355V136L367 110V91Z" fill="#dcecff"/>
        <path d="M369 92H391V109H369Z M356 139H404V157H356Z M356 205H404V219H356Z M356 288H404V307H356Z" fill="var(--ear)"/>
        <path d="M369 113H391L401 134H359Z" fill="#dcecff"/>
        <path d="M356 160H364V201H356Z M396 160H404V201H396Z M355 244H365V287H355Z M375 244H385V287H375Z M395 244H405V287H395Z" fill="var(--ear)"/>
        <path d="M355 277L338 313H355Z M405 277L422 313H405Z" fill="var(--ear)"/>
        <path d="M359 307L355 322H368L366 307M375 307L372 325H388L385 307M394 307L392 322H405L401 307" fill="var(--ear)"/>
        <path d="M355 137H405M355 159H405M355 203H405M355 222H405M355 286H405" stroke="var(--muted)" stroke-width="2"/>
        <path d="M376 171V180H383V171M383 185H376V189H383V193H376M376 205V198H383V205M376 201H383" fill="none" stroke="var(--ear)" stroke-width="1.8"/>
        <path d="M374 228H386V236H374Z" fill="#dcecff"/>
        <path d="M374 228H379V232H374Z" fill="var(--ear)"/>
        <path d="M380 230H386M374 234H386" stroke="var(--ear)" stroke-width="1"/>
        </g>
    ''',
    'bunker_hill': '<path d="M322 309L337 96 380 33 423 96 438 309Z"/><path d="M311 310H449V329H311Z" fill="var(--ear)"/><path d="M380 39V309" stroke="var(--ear)" stroke-width="5"/>',
    'eiffel': '''
        <path d="M376 27H384L391 106 407 168 431 223 493 322H453L418 260Q380 218 342 260L307 322H267L329 223 353 168 369 106Z"/>
        <path d="M377 74H383L383 108H377Z M376 119H384L396 166H364Z M362 179H398L416 221H344Z" fill="var(--panel)"/>
        <g fill="none" stroke="var(--ear)" stroke-width="4">
          <path d="M370 119L390 141 361 163M389 119L369 142 399 163M353 180L405 213M406 180L354 213
                   M333 234L335 270 303 277 309 310M426 234L424 270 456 277 450 310
                   M321 252L344 251M306 278L325 280M439 251L416 251M454 278L435 280"/>
        </g>
        <path d="M376 116L388 132M370 143L394 159M357 181L406 216M402 181L353 216" stroke="var(--animal)" stroke-width="4"/>
        <path d="M360 108H400V117H360Z M343 166H417V178H343Z M318 219H442V233H318Z M263 321H311V330H263Z M449 321H497V330H449Z" fill="var(--ear)"/>
        <path d="M380 15V29" stroke="var(--ear)" stroke-width="4"/>
    ''',
    'pisa': '''
        <g transform="rotate(9 380 320)">
          <path d="M310 318V111Q380 83 450 111V318Z"/>
          <path d="M334 103V70Q380 49 426 70V103Z"/>
          <ellipse cx="380" cy="68" rx="46" ry="10" fill="var(--ear)"/>
          <path d="M306 310Q380 330 454 310V326Q380 346 306 326Z" fill="var(--ear)"/>
          <path d="M307 113Q380 132 453 113" fill="none" stroke="var(--ear)" stroke-width="5"/><path d="M318 138V125Q324 116 330 125V138" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M340 142V129Q346 120 352 129V142" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M362 144V131Q368 122 374 131V144" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M384 144V131Q390 122 396 131V144" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M406 142V129Q412 120 418 129V142" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M428 138V125Q434 116 440 125V138" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M307 143Q380 162 453 143" fill="none" stroke="var(--ear)" stroke-width="5"/><path d="M318 168V155Q324 146 330 155V168" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M340 172V159Q346 150 352 159V172" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M362 174V161Q368 152 374 161V174" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M384 174V161Q390 152 396 161V174" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M406 172V159Q412 150 418 159V172" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M428 168V155Q434 146 440 155V168" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M307 173Q380 192 453 173" fill="none" stroke="var(--ear)" stroke-width="5"/><path d="M318 198V185Q324 176 330 185V198" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M340 202V189Q346 180 352 189V202" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M362 204V191Q368 182 374 191V204" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M384 204V191Q390 182 396 191V204" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M406 202V189Q412 180 418 189V202" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M428 198V185Q434 176 440 185V198" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M307 203Q380 222 453 203" fill="none" stroke="var(--ear)" stroke-width="5"/><path d="M318 228V215Q324 206 330 215V228" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M340 232V219Q346 210 352 219V232" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M362 234V221Q368 212 374 221V234" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M384 234V221Q390 212 396 221V234" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M406 232V219Q412 210 418 219V232" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M428 228V215Q434 206 440 215V228" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M307 233Q380 252 453 233" fill="none" stroke="var(--ear)" stroke-width="5"/><path d="M318 258V245Q324 236 330 245V258" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M340 262V249Q346 240 352 249V262" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M362 264V251Q368 242 374 251V264" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M384 264V251Q390 242 396 251V264" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M406 262V249Q412 240 418 249V262" fill="none" stroke="var(--ear)" stroke-width="3.5"/><path d="M428 258V245Q434 236 440 245V258" fill="none" stroke="var(--ear)" stroke-width="3.5"/>
          <path d="M362 317V292Q380 272 398 292V317Z" fill="var(--ear)"/>
          <path d="M320 294V279Q328 269 336 279V299M424 299V279Q432 269 440 279V294" fill="none" stroke="var(--ear)" stroke-width="4"/>
          <path d="M346 96V79Q351 72 356 79V98M368 100V78Q374 71 380 78V101M392 100V78Q398 71 404 78V98M415 96V79" fill="none" stroke="var(--ear)" stroke-width="4"/>
          <path d="M331 102Q380 116 429 102" fill="none" stroke="var(--ear)" stroke-width="6"/>
        </g>
    ''',
    'washington': '<path d="M337 309L352 89 380 27 408 89 423 309Z"/><path d="M307 311H453V333H307Z M380 28L408 89 423 309H380Z" fill="var(--ear)"/>',
    # Charles de Gaulle silhouette adapted from TheFrenchKing (CC BY-SA 4.0).
    # Source, changes, and license: assets/carrier-LICENSE.txt.
    'carrier': '''
        <!-- Aircraft carrier silhouette: TheFrenchKing, CC BY-SA 4.0.
             https://commons.wikimedia.org/wiki/File:Flugzeugtr%C3%A4ger_Silhouette_(version_2).svg
             https://creativecommons.org/licenses/by-sa/4.0/
             Adapted with palette, hull shading, windows, and parked aircraft. -->
        <g transform="translate(80 125) scale(.245)">
            <g transform="matrix(-1,0,0,1,1253.2032,353.02414)">
                <path fill-rule="evenodd" d="m 354.11667,-352.86797 v 24.68007 h -26.574 v 7.59089 h 26.574 v 118.15711 l -103.4699,-0.44979 1.8996,10.43728 34.1723,2.84586 64.552,14.24252 h 22.7814 l 3.7992,85.429729 h -24.6812 l 3.7993,47.46016 h -36.6223 l 3.806,-54.07157 c 1.5585,-3.15992 2.4366,-6.717769 2.4364,-10.477239 0,-13.09899 -10.628,-23.72677 -23.7278,-23.72677 -13.0998,0 -23.7346,10.62752 -23.7346,23.72677 0,3.80868 0.8997,7.407279 2.4969,10.597889 -0.6871,15.90357 -9.5147,49.21911 -10.7867,53.95092 h -0.2552 l 0.047,0.76491 c 0,0.0132 -0.047,0.18151 -0.047,0.18151 l 0.054,-0.0738 4.5107,70.31408 h -34.9374 v 11.39005 h 3.8998 l 4.6451,10.44363 -52.6713,2.77231 -9.9813,-34.09659 h -5.6986 c 0,0 2.6627,9.76788 -6.6049,37.02314 h -4.7858 v 6.64475 h 7.598 v 0.94615 h -10.4441 v 10.4439 h 10.4441 v 19.927892 l -258.201297,3.79888 v 1.89945 H -1182.7346 c -14.1937,1.446469 -15.5132,9.327089 -9.4913,20.880919 l 22.7814,18.98782 v 13.28976 l -11.3907,17.08176 v 30.3784 h 15.19 l 11.3907,49.35961 c 0,0 25.3366,-1.36287 36.0719,0 18.0895,2.29659 40.8724,12.15152 58.8534,15.18259 12.6384,2.13016 27.6273,2.06269 42.7169,2.20133 v 4.44341 h 31.23219 l -4.6382,7.07417 c -1.2548,1.91267 -1.6447,4.13835 -1.2686,6.21533 h -18.68029 v 30.3784 h 33.22589 v -18.03506 c 3.5667,1.14617 7.5798,-0.15875 9.7394,-3.4499 l 11.0753,-16.87381 c 12.5676,6.24708 25.66224,15.88982 35.18595,24.11598 1.23251,1.06468 2.58506,2.35717 4.00719,3.79889 h -19.1905 v -14.23617 h -8.54464 v 41.76183 h 8.54464 v -18.98147 h 26.99693 c 10.09078,11.67686 20.46552,25.62622 20.46573,25.62622 l 1985.84971,-5.69172 55.0611,-11.39005 3.7925,-102.5181 c 32.2472,-38.10689 59.5723,-70.44717 96.8246,-83.53029 l -1.8997,-41.768179 h -121.4988 l -5.6989,1.89918 -527.78693,-3.792012 15.1831,-55.05821 -7.5917,-7.59116 h -100.6239 l 3.7992,-22.7803603 9.4913,-13.2894902 -1.8929,-9.4908705 11.3907,-28.478429 7.5916,-1.89971 -3.7993,-15.1892 h -9.491 v -9.4906 h -25.6277 v -38.915719 h -18.989 v -9.4906 h 40.8176 v -5.69833 h -37.0183 v -27.52567 h -17.0896 v 29.42511 h 5.6986 v 3.79889 h 1.8997 v 9.4906 h -4.7457 v 19.934509 l -41.7704,-3.79889 3.7991,-85.429729 34.1723,-1.89944 5.692,-20.88092 -2.6581,-0.0132 c 2.8821,-4.3516 4.5577,-9.56945 4.5577,-15.17597 0,-15.19476 -12.3312,-27.5254 -27.5272,-27.5254 -15.1958,0 -27.527,12.33064 -27.527,27.5254 0,5.52106 1.6281,10.6635 4.4301,14.97436 l -57.5914,-0.24818 v -118.19071 h 10.4443 v -7.59089 h -10.4443 v -24.68007 h -6.6451 z m -41.247,267.363319 6.249,43.03051 h -47.8249 l 30.8026,-40.82891 c 0.2528,0.008 0.5105,0.0132 0.7653,0.0132 3.5765,0 6.9655,-0.79587 10.008,-2.21483 z m -127.7215,120.86194 9.7664,18.02156 -18.3045,0.96679 v 1.89944 h -2.3223 z"/>
            </g>
        </g>
        <path d="M105 275Q286 287 626 275L611 294H121L105 290Z" fill="var(--ear)"/>
        <path d="M85 237H675" fill="none" stroke="var(--ear)" stroke-width="6"/>
        <path d="M119 251H211V268H119Z M369 250H421V269H369Z M482 250H535V269H482Z" fill="var(--ear)"/>
        <path d="M126 254H204M376 254H414M489 254H528" stroke="var(--muted)" stroke-width="3"/>
        <path d="M238 239V264H274V239M552 239V264H588V239" fill="none" stroke="var(--ear)" stroke-width="3"/>
        <path d="M258 202H297V211H258Z M301 212H328V219H301Z" fill="var(--panel)"/>
        <path d="M270 202V211M283 202V211M313 212V219" stroke="var(--animal)" stroke-width="3"/>
        <path d="M261 221H289M304 226H329" stroke="var(--ear)" stroke-width="3"/>
        <path d="M281 172V187M274 179H288" stroke="var(--ear)" stroke-width="3"/>
    ''' + ''.join(
        f'<g transform="translate({x} 234)">'
        '<path d="M-24 -7L-15 -13H9L17 -24H23L20 -9 28 -5 12 -3H-20Z" fill="var(--ear)"/>'
        '<path d="M-6 -10L10 -4H17L5 -13Z" fill="var(--animal)"/>'
        '<path d="M-15 -12H-6V-9H-19Z" fill="#dcecff"/>'
        '<path d="M-12 -3V0M15 -3V0" stroke="var(--ear)" stroke-width="3"/>'
        '</g>' for x in (153, 211, 393, 455, 517, 579, 641)
    ) + '''
        <path d="M97 305Q193 312 280 306M467 306Q568 311 645 302" fill="none" stroke="var(--animal)" stroke-width="4" opacity=".4"/>
    ''',
    'empire_state': '<path d="M282 325V196H311V134H335V84H360V52H400V84H425V134H449V196H478V325Z"/><path d="M380 16V59" stroke="var(--accent)" stroke-width="7"/>'+''.join(f'<path d="M{x} 156V309" stroke="var(--ear)" stroke-width="6"/>' for x in range(329,443,18)),
    'golden_gate': '<path d="M220 93V320M259 93V320M500 93V320M539 93V320M220 129H259M220 189H259M500 129H539M500 189H539" stroke="var(--animal)" stroke-width="15"/><path d="M89 278H671" stroke="var(--ear)" stroke-width="16"/><path d="M89 249Q148 219 239 101Q380 365 519 101Q609 219 671 249" fill="none" stroke="var(--accent)" stroke-width="6"/>'+''.join(f'<path d="M{x} {int(110+155*(1-((x-380)/140)**2))}V271" stroke="var(--ear)" stroke-width="3"/>' for x in range(280,500,25)),
    'pyramid': '<path d="M124 316L380 52 639 316Z"/><path d="M380 52L433 316H639Z" fill="var(--ear)"/><path d="M205 274H418M247 231H408M290 187H400M332 143H392" stroke="var(--ear)" stroke-width="4"/>',
}
