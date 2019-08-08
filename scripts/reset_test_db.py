import os

if os.path.exists('mcp/site.db'):
    os.system('rm mcp/site.db')
if os.path.exists('migrations/'):
    os.system('rm -r migrations/versions/*')
else:
    os.system('flask db init')
os.system('flask db migrate')
os.system('flask db upgrade')
