from mcp.wildeapricot import create_app, db, cli

app = create_app()
cli.register(app)

if __name__ == '__main__':
   print("start")
   mcp.wildapricot.routes.pull_groups()
   print("end")

