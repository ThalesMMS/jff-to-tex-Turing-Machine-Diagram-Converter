import xml.etree.ElementTree as ET
import sys
import os

def parse_jff(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    automaton = root.find('automaton')
    
    states = {}
    transitions = []
    
    # Scale factor: JFLAP uses pixels, LaTeX/TikZ works better with cm
    # Typically dividing by 100 is a good start. 
    # Also JFLAP (0,0) is top-left, but TikZ is bottom-left (Cartesian). 
    # We might need to flip Y, but let's try just scaling first.
    # Usually relative placement is what matters more than absolute.
    SCALE = 0.02
    
    for state in automaton.findall('state'):
        s_id = state.get('id')
        name = state.get('name')
        x = float(state.find('x').text) * SCALE
        # Inverting Y because JFLAP is top-down (screen coords), TikZ is bottom-up (Cartesian)
        # We'll pick an arbitrary offset (e.g. 10) to keep values positive if needed, 
        # or just flip it relative to the first node.
        # Let's just create them as -y for now to preserve relative structure visually.
        y = -float(state.find('y').text) * SCALE
        
        is_initial = state.find('initial') is not None
        is_final = state.find('final') is not None
        
        states[s_id] = {
            'name': name,
            'x': x,
            'y': y,
            'initial': is_initial,
            'final': is_final
        }
        
    for trans in automaton.findall('transition'):
        f = trans.find('from').text
        t = trans.find('to').text
        read = trans.find('read').text if trans.find('read').text else "\\blank"
        write = trans.find('write').text if trans.find('write').text else "\\blank"
        move = trans.find('move').text
        
        transitions.append({
            'from': f,
            'to': t,
            'read': read,
            'write': write,
            'move': move
        })
        
    return states, transitions

def generate_latex(states, transitions):
    latex = []
    latex.append(r"\documentclass{article}")
    latex.append(r"\usepackage[utf8]{inputenc}")
    latex.append(r"\usepackage{tikz}")
    latex.append(r"\usepackage{amssymb}")
    latex.append(r"\usetikzlibrary{automata, positioning, arrows}")
    latex.append(r"\newcommand{\blank}{\square}")
    latex.append(r"\begin{document}")
    latex.append(r"\begin{center}")
    latex.append(r"\begin{tikzpicture}[>=stealth, auto, node distance=2cm, thick]")
    
    # Generate States
    for s_id, data in states.items():
        style = "state"
        if data['initial']:
            style += ", initial"
        if data['final']:
            style += ", accepting"
            
        # Using 'at' syntax for absolute positioning based on JFLAP coords
        latex.append(f"    \\node[{style}] ({s_id}) at ({data['x']:.2f}, {data['y']:.2f}) {{${data['name']}$}};")
        
    latex.append("")
    
    # Group transitions by (from, to) to combine labels
    grouped_trans = {}
    for t in transitions:
        key = (t['from'], t['to'])
        # Wrap read/write in $...$ for math mode (needed for \blank=\square)
        label = f"${t['read']}$/${t['write']}$ {t['move']}"
        if key not in grouped_trans:
            grouped_trans[key] = []
        grouped_trans[key].append(label)
        
    # Generate Transitions
    latex.append(r"    \path[->]")
    for (src, dst), labels in grouped_trans.items():
        label_text = r" \\ ".join(labels)
        
        # Simple heuristic for loops and styling
        options = ""
        if src == dst:
            options = "loop above"
        else:
            # Check for bidirectional transitions (A -> B and B -> A)
            # If so, bend right to avoid overlap
            if (dst, src) in grouped_trans:
                options = "bend right"
            else:
                options = "" # straight line by default
                
        latex.append(f"        ({src}) edge[{options}] node[align=center] {{{label_text}}} ({dst})")
        
    latex.append(r"    ;")
    latex.append(r"\end{tikzpicture}")
    latex.append(r"\end{center}")
    latex.append(r"\end{document}")
    
    return "\n".join(latex)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python converter.py <input.jff>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    states, transitions = parse_jff(input_file)
    latex_code = generate_latex(states, transitions)
    
    output_file = os.path.splitext(input_file)[0] + ".tex"
    with open(output_file, "w") as f:
        f.write(latex_code)
        
    print(f"Converted {input_file} to {output_file}")
