import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/cayecaji/tfg_edge__GPU/src/install/action_recognition'
