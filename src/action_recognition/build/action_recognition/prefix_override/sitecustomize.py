import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/cayecaji/tfg/src/action_recognition/install/action_recognition'
