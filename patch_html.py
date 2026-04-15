import re

with open("maer_backend/web_ui/static/index.html", "r") as f:
    text = f.read()

# Reemplazar inputs por grupos de flexbox con boton
def replace_input(match):
    full_line = match.group(0)
    id_name = match.group(1)
    
    # Si ya esta modificado (tiene flexbox antes), saltar
    if "display: flex" in text[text.find(full_line)-50:text.find(full_line)]:
        return full_line

    btn_type = "dir" if "dir" in id_name else "file"
    
    return f'<div style="display: flex; gap: 0.5rem;">\n{full_line}\n<button class="btn btn-secondary btn-pick-{btn_type}" data-target="{id_name}" title="Explorar Mac" style="padding: 0 1rem;">📁</button>\n</div>'

pattern = r'(\s*)<input type="text" id="([^"]+)" class="input" placeholder="[^"]+">'
# Actually, just regex replace the exact line
lines = text.split('\n')
out = []
for i, line in enumerate(lines):
    if '<input type="text" id=' in line and 'class="input"' in line:
        id_match = re.search(r'id="([^"]+)"', line)
        if id_match:
            id_name = id_match.group(1)
            btn_type = "dir" if id_name.endswith('dir') else "file"
            
            # wrap in flex
            ws = line[:len(line) - len(line.lstrip())]
            out.append(ws + '<div style="display: flex; gap: 0.5rem;">')
            out.append(line)
            out.append(ws + f'    <button class="btn btn-secondary btn-pick-{btn_type}" data-target="{id_name}" title="Explorar Archivos en Mac">📁 Buscar</button>')
            out.append(ws + '</div>')
            continue
    out.append(line)

text = '\n'.join(out)

# Insert Chat option
if '<option value="chat">' not in text:
    text = text.replace(
        '<option value="extract_json">Extraer Estructura de Datos (JSON)</option>',
        '<option value="extract_json">Extraer Estructura de Datos (JSON)</option>\n                        <option value="chat">Conversación Abierta / Preguntar</option>'
    )
    # also standard placeholders if it's the old text
    text = text.replace(
        '<option value="extract_json">Extraer a JSON</option>',
        '<option value="extract_json">Extraer a JSON</option>\n                        <option value="chat">Conversación Abierta / Preguntar</option>'
    )

with open("maer_backend/web_ui/static/index.html", "w") as f:
    f.write(text)

