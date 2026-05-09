import json
import os
import sys

# Add the current directory to path so we can import the bot if needed
sys.path.append(os.getcwd())

def generate_commands_json():
    """
    This script parses the cogs directory and extracts command information.
    Note: A better way would be to run the bot and extract them, 
    but this static analysis approach is safer for a standalone script.
    """
    commands_list = []
    cogs_dir = './cogs'
    
    if not os.path.exists(cogs_dir):
        print("Cogs directory not found.")
        return

    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            cog_name = filename[:-3]
            file_path = os.path.join(cogs_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple heuristic to find commands in the file
            # This is not perfect but works for the current structure
            lines = content.split('\n')
            current_category = cog_name.lower()
            
            for i, line in enumerate(lines):
                if '@commands.command' in line or '@commands.group' in line:
                    # Find the function definition on the next few lines
                    for j in range(i + 1, i + 5):
                        if j < len(lines) and 'async def ' in lines[j]:
                            func_line = lines[j]
                            cmd_name = func_line.split('async def ')[1].split('(')[0].strip()
                            
                            # Try to find a description or docstring
                            description = "No description provided."
                            # Check for docstring
                            for k in range(j + 1, j + 5):
                                if k < len(lines) and '"""' in lines[k]:
                                    description = lines[k].replace('"""', '').strip()
                                    break
                            
                            # Check for help= in the decorator
                            if 'help="' in line:
                                description = line.split('help="')[1].split('"')[0]
                            elif "help='" in line:
                                description = line.split("help='")[1].split("'")[0]
                            
                            # Basic usage guess
                            usage = f",{cmd_name}"
                            if '(' in func_line:
                                args = func_line.split('(')[1].split(')')[0].split(',')
                                for arg in args:
                                    arg = arg.strip()
                                    if arg not in ['self', 'ctx', 'ctx: commands.Context', 'member: discord.Member = None', 'member: discord.Member']:
                                        if ':' in arg:
                                            arg_name = arg.split(':')[0].strip()
                                            usage += f" <{arg_name}>"
                                        elif '=' in arg:
                                            arg_name = arg.split('=')[0].strip()
                                            usage += f" [{arg_name}]"
                                        elif arg:
                                            usage += f" <{arg}>"
                            
                            commands_list.append({
                                "name": cmd_name,
                                "description": description,
                                "category": current_category,
                                "usage": usage
                            })
                            break
                            
    # Save to flaw web/commands.json
    web_dir = './flaw web'
    if not os.path.exists(web_dir):
        os.makedirs(web_dir)
        
    output_path = os.path.join(web_dir, 'commands.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(commands_list, f, indent=4)
        
    print(f"Successfully generated {len(commands_list)} commands in {output_path}")

if __name__ == "__main__":
    generate_commands_json()
