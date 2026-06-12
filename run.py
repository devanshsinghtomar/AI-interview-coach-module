#!/usr/bin/env python3
import os
import sys
from flask import Flask, render_template_string

# Read the original app
with open('app.py', 'r') as f:
    app_code = f.read()

# Execute original app setup
exec(app_code)

# Fix the template issue by overriding render_template
original_render = app.render_template

def fixed_render(template_name, **context):
    if template_name == 'index.html':
        # Create a fixed version in memory
        with open('templates/base.html', 'r') as f:
            base_content = f.read()
        
        # Remove duplicate content blocks
        lines = base_content.split('\n')
        unique_lines = []
        found_content = False
        
        for line in lines:
            if 'block content' in line:
                if not found_content:
                    unique_lines.append(line)
                    found_content = True
            else:
                unique_lines.append(line)
        
        fixed_base = '\n'.join(unique_lines)
        
        # Write fixed version temporarily
        with open('templates/base_fixed.html', 'w') as f:
            f.write(fixed_base)
        
        # Override the extends
        with open('templates/index.html', 'r') as f:
            index_content = f.read()
        
        fixed_index = index_content.replace('base.html', 'base_fixed.html')
        
        # Render from string
        return render_template_string(fixed_index, **context)
    
    return original_render(template_name, **context)

app.render_template = fixed_render

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
