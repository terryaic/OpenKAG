
llama_prompt_template="""
<s>[INST] <<SYS>>
*system_prompt*
<</SYS>>
*user_message*
[/INST]
"""

zephyr_prompt_template = 'User: *system_prompt*\n\n*user_message*\n\nAssistant:'

llama_prompt_format="""
<s>[INST] <<SYS>>
%s
<</SYS>>
%s
[/INST]
"""
zephyr_prompt_format = 'User: %s\n\n%s\n\nAssistant:'

def get_format(model_name):
    if model_name.find('zephyr') >= 0:
        return zephyr_prompt_format
    else:
        return llama_prompt_format

def get_prompt(model_name):
    if model_name.find('zephyr') >= 0:
        return zephyr_prompt_template
    else:
        return llama_prompt_template