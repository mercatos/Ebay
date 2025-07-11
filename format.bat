rem [build] cmd.exe /c format.bat

yapf --style "{based_on_style: google, indent_width: 2, column_limit: 111, blank_lines_around_top_level_definition: 1}" --in-place proto.py
