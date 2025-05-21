import glob
import os
from pathlib import Path

# Debug message for dockerfile build
print ("the script has succesfully started")

# create the output directory
Path('pxc_grpc').mkdir(parents=True, exist_ok=True)

grpc_command_base = 'python3 -m grpc_tools.protoc -I./include/google/protobuf --python_out=pxc_grpc --grpc_python_out=pxc_grpc '


import_paths = set()

# Debug message for dockerfile build
print ("the Code snippets are about to be created")
# generate the *_pb2.py and *_pb2_grpc.py files
for filename in glob.iglob('./include/google/protobuf/**', recursive=True):

    if filename.endswith('.proto'):
        
        # store the import path
        path_parts = filename.split(os.sep)
        import_paths.add('.'.join(path_parts[1:-1]))

        grpc_command = ''.join([grpc_command_base, os.path.join('.', os.path.relpath(filename))])
        stream = os.popen(grpc_command)
        output = stream.read()
        print ("Working!")
        if output != '':
            print(''.join(['error/info for file ', os.path.relpath(filename), ' - ', output]))


# get the python files in the base directory
base_pys = set()

for (dirpath, dirnames, filenames) in os.walk('./pxc_grpc'):
    for f in filenames:
        base_pys.add(f.split('.py')[0])
        print ("Working!")
    break

# reformat the stored paths to adapt the import statements
try:
    import_paths.remove('')
except:
    pass

import_paths = list(import_paths)
import_paths.sort(key=len)
import_paths.reverse()

# adapt the imports
for filename in glob.iglob('./pxc_grpc/**', recursive=True):

    if filename.endswith('.py'):

        new_lines = []

        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith('from'):
                    for import_path in import_paths:
                        if import_path in line:
                            line = line.replace(import_path, ''.join(['pxc_grpc.', import_path]), 1)
                            print ("Working!")
                            break
                elif line.startswith('import'):
                    parts = line.split()
                    if parts[1] in base_pys:
                        line = line.replace('import', 'from pxc_grpc import')
                
                new_lines.append(line)

        with open(filename, 'w') as file:
            file.write(''.join(new_lines))
