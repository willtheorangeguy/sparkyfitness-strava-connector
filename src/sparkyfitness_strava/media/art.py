"""Original schematic vector artwork. Muscle areas indicate metadata, not intensity."""

# The left half of an athletic silhouette; mirror around x=100 for the right half.
OUTLINE = 'M100 12 C87 12 81 22 82 36 L85 48 91 54 89 65 C79 70 64 70 56 80 C49 90 48 104 45 119 L36 150 27 182 21 199 23 208 29 202 32 190 36 194 41 188 43 175 58 142 64 117 68 146 73 163 69 188 66 210 68 241 73 273 71 294 68 324 69 351 64 368 66 375 82 375 87 369 84 353 87 323 89 296 90 276 95 238 100 211'
FRONT = {
 'shoulders': 'M59 81 C65 75 74 73 79 76 L76 97 61 108 53 102 C53 92 55 86 59 81Z',
 'chest': 'M79 77 L96 73 98 107 Q88 119 74 108 L77 94Z',
 'biceps': 'M57 110 L68 103 64 123 54 143 47 142 50 127Z',
 'triceps': 'M49 110 L55 109 47 138 43 142 44 128Z',
 'forearms': 'M46 146 L53 149 39 180 32 187 33 178Z',
 'abs': 'M85 117 L98 115 98 130 85 130Z M84 134 L98 134 98 149 83 148Z M83 152 L98 153 98 171 87 168Z',
 'obliques': 'M73 114 L81 121 79 150 86 173 76 165 70 144Z',
 'quads': 'M76 176 L94 185 93 207 86 243 78 267 73 245 70 212Z',
 'adductors': 'M96 184 L99 205 93 242 88 262 85 244Z',
 'calves': 'M75 279 L85 278 84 306 77 334 72 322Z',
}
BACK = {
 'back': 'M91 64 L98 65 98 94 79 87Z M77 94 L97 100 96 128 81 151 72 127Z',
 'shoulders': 'M59 81 Q68 74 78 77 L74 98 61 109 53 102 Q53 89 59 81Z',
 'triceps': 'M57 111 L67 106 63 127 54 145 47 141Z',
 'forearms': 'M46 148 L53 150 39 179 32 187 34 175Z',
 'lower_back': 'M89 135 L98 130 98 167 79 172 78 157Z',
 'glutes': 'M76 176 Q84 169 98 174 L98 202 Q89 218 71 210Z',
 'hamstrings': 'M72 218 Q85 223 96 211 L90 246 83 269 75 268 70 244Z',
 'calves': 'M74 280 L86 278 85 307 79 330 74 338 71 321Z',
}


def body(primary, secondary, back=False):
    paths = BACK if back else FRONT
    result = ['<svg viewBox="0 0 200 390" role="img" aria-label="'+('Back' if back else 'Front')+' muscle diagram">']
    for mirror in ('', 'translate(200 0) scale(-1 1)'):
        result.append(f'<g transform="{mirror}"><path class="body-base" d="{OUTLINE}Z"/>')
        for muscle, path in paths.items():
            level = 'primary' if muscle in primary else 'secondary' if muscle in secondary else 'inactive'
            result.append(f'<path class="muscle {level}" data-muscle="{muscle}" d="{path}"/>')
        result.append('</g>')
    detail = 'M100 58V173' if back else 'M100 58V173 M85 51Q100 60 115 51 M91 28Q100 23 109 28'
    result.append('<path class="body-detail" d="'+detail+'"/></svg>')
    return ''.join(result)


def elephant():
    return '''<svg viewBox="0 0 760 370" role="img" aria-label="Original elephant illustration">
      <ellipse cx="372" cy="337" rx="275" ry="11" fill="currentColor" opacity=".07"/>
      <path class="animal-back" d="M200 239L199 323Q219 338 244 323L254 247 M456 235L468 324Q491 339 510 321L512 229"/>
      <path class="animal-body" d="M174 242Q126 153 204 92Q268 43 416 62Q487 58 529 109Q561 89 608 112Q649 139 637 188L642 246Q651 280 677 254Q692 244 700 258Q697 298 660 306Q605 315 590 259L581 224L548 240L539 324Q521 345 494 329L478 266Q425 292 326 276L304 327Q279 343 256 325L258 266L205 264Q177 255 174 242Z"/>
      <path class="animal-ear" d="M511 122Q436 99 427 174Q421 229 487 250Q530 242 540 187Q547 143 511 122Z"/>
      <path class="animal-line" d="M177 164Q150 171 143 203L130 235 M528 125Q555 155 548 190 M453 143Q432 184 466 215"/>
      <path class="animal-tusk" d="M600 206Q626 233 650 215Q634 246 606 234Z"/>
      <circle cx="598" cy="159" r="5" class="animal-eye"/>
    </svg>'''
