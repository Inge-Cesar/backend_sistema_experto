import glob
import os

replacements = {
    "modules.base_conocimiento": "modules.base_conocimiento",
    "modules.personal": "modules.personal",
    "modules.turnos": "modules.turnos",
    "modules.motor_experto": "modules.motor_experto",
    "modules.usuarios": "modules.usuarios"
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Modificado: {filepath}")

for root, dirs, files in os.walk('.'):
    if '.venv' in root or '__pycache__' in root or 'migrations' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            process_file(filepath)

print("Proceso de reemplazo finalizado.")
