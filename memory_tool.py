import os

def modify_memory(file_path='memory.md', action='append', content=None):
    """
    Tool to modify memory.md file containing user information.
    - action: 'append' (add new info), 'read' (get content), 'overwrite' (replace all), 'edit' (replace specific line).
    - content: For append/overwrite: new text. For edit: dict {'old_line': 'new_line'}.
    """
    if not os.path.exists(file_path) and action != 'overwrite':
        with open(file_path, 'w') as f:
            f.write('# User Memory\n')
    
    if action == 'read':
        with open(file_path, 'r') as f:
            return f.read()
    
    elif action == 'append':
        if content:
            with open(file_path, 'a') as f:
                f.write(f'\n{content}')
        else:
            raise ValueError("Content required for append.")
    
    elif action == 'overwrite':
        if content:
            with open(file_path, 'w') as f:
                f.write(content)
        else:
            raise ValueError("Content required for overwrite.")
    
    elif action == 'edit':
        if isinstance(content, dict):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            with open(file_path, 'w') as f:
                for line in lines:
                    for old, new in content.items():
                        if old in line:
                            line = line.replace(old, new)
                    f.write(line)
        else:
            raise ValueError("Content must be a dict for edit.")
    
    else:
        raise ValueError("Invalid action.")

# Example usage:
# modify_memory(action='append', content='User prefers French responses.')
# print(modify_memory(action='read'))
